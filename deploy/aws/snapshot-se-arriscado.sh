#!/usr/bin/env bash
# Snapshot do RDS antes da migração, só quando ela for arriscada.
#
# Compara as migrações entre o último commit implantado com sucesso
# (guardado no SSM Parameter Store) e o commit atual. Se alguma migração
# nova contiver operação destrutiva ou que reescreve dados, tira um
# snapshot manual do RDS e espera ficar disponível antes de seguir.
#
# Fail-closed: na dúvida, o deploy para ou o snapshot é tirado.
# - Só "ParameterNotFound" conta como primeiro deploy. Acesso negado,
#   timeout ou falha de rede ao ler o SSM interrompem o deploy.
# - Migração já aplicada que foi alterada, removida ou renomeada
#   interrompe o deploy: o Prisma registra checksum das aplicadas.
#
# Modos (variável MODO): auto (padrão) | sempre | nunca
#
# Variáveis obrigatórias: DB_INSTANCE_ID, AWS_REGION, PARAM_ULTIMO_DEPLOY
# Saída: imprime "snapshot=<id>" ou "snapshot=nenhum" (e grava em $GITHUB_OUTPUT, se existir)
set -euo pipefail

: "${DB_INSTANCE_ID:?}" "${AWS_REGION:?}" "${PARAM_ULTIMO_DEPLOY:?}"
MODO="${MODO:-auto}"
PASTA="server/prisma/migrations"
# Operações que destroem ou reescrevem dados, ou quebram a versão anterior da API.
# UPDATE só no início da linha (com ou sem aspas), para não confundir com
# "ON UPDATE CASCADE" das chaves estrangeiras.
PADRAO='DROP[[:space:]]+(TABLE|COLUMN|SCHEMA|TYPE|INDEX|CONSTRAINT)|TRUNCATE|DELETE[[:space:]]+FROM|^[[:space:]]*UPDATE[[:space:]]|ALTER[[:space:]]+COLUMN[^;]*[[:space:]]TYPE|ALTER[[:space:]]+COLUMN[^;]*SET[[:space:]]+NOT[[:space:]]+NULL|RENAME[[:space:]]+(COLUMN|TO)'

saida() {
  echo "snapshot=$1"
  if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "snapshot=$1" >> "$GITHUB_OUTPUT"; fi
}

# Lê o último deploy. Imprime o SHA, ou nada se o parâmetro não existir.
# Qualquer outro erro encerra o script com código 1.
ler_ultimo_deploy() {
  local out err rc
  err=$(mktemp)
  set +e
  out=$(aws ssm get-parameter --name "$PARAM_ULTIMO_DEPLOY" --query Parameter.Value --output text 2>"$err")
  rc=$?
  set -e
  if [ $rc -eq 0 ]; then echo "$out"; rm -f "$err"; return 0; fi
  if grep -q 'ParameterNotFound' "$err"; then rm -f "$err"; return 0; fi
  echo "::error::Falha ao ler $PARAM_ULTIMO_DEPLOY no SSM (não é ParameterNotFound); deploy interrompido." >&2
  cat "$err" >&2; rm -f "$err"
  exit 1
}

decidir() {
  case "$MODO" in
    sempre) echo "Modo 'sempre'."; return 0 ;;
    nunca)  echo "Modo 'nunca'."; return 1 ;;
    auto)   ;;
    *) echo "::error::MODO inválido: $MODO"; exit 2 ;;
  esac

  ULTIMO=$(ler_ultimo_deploy) || exit 1
  if [ -z "$ULTIMO" ]; then
    echo "Parâmetro de último deploy inexistente (primeiro deploy): banco ainda vazio, snapshot dispensado."
    return 1
  fi
  if ! git cat-file -e "${ULTIMO}^{commit}" 2>/dev/null; then
    echo "::warning::Commit do último deploy ($ULTIMO) não está no histórico local; por segurança, tira snapshot."
    return 0
  fi

  # Migrações aplicadas não podem mudar: alteração, remoção ou renomeação é erro.
  ALTERADAS=$(git diff --name-status -M "$ULTIMO" HEAD -- "$PASTA" | awk '$1 ~ /^(M|D|R)/ && $0 ~ /migration\.sql/')
  if [ -n "$ALTERADAS" ]; then
    echo "::error::Migração já aplicada foi alterada, removida ou renomeada desde $ULTIMO; deploy interrompido:"
    echo "$ALTERADAS" | sed 's/^/  /'
    exit 1
  fi

  NOVAS=$(git diff --name-only --diff-filter=A "$ULTIMO" HEAD -- "$PASTA" | grep 'migration.sql$' || true)
  if [ -z "$NOVAS" ]; then
    echo "Nenhuma migração nova desde $ULTIMO."
    return 1
  fi
  echo "Migrações novas desde $ULTIMO:"; echo "$NOVAS" | sed 's/^/  /'

  ARRISCADAS=""
  for f in $NOVAS; do
    if grep -Eiq "$PADRAO" "$f"; then ARRISCADAS="$ARRISCADAS $f"; fi
  done
  if [ -n "$ARRISCADAS" ]; then
    echo "Operações arriscadas encontradas em:$ARRISCADAS"
    for f in $ARRISCADAS; do grep -Ein "$PADRAO" "$f" | sed "s|^|  $f:|"; done
    return 0
  fi
  echo "Migrações novas só aditivas (CREATE, ADD COLUMN, índices): snapshot dispensado."
  return 1
}

if decidir; then
  ID="${DB_INSTANCE_ID}-pre-migracao-$(date -u +%Y%m%d-%H%M%S)"
  echo "Criando snapshot $ID..."
  aws rds create-db-snapshot --region "$AWS_REGION" --db-instance-identifier "$DB_INSTANCE_ID" \
    --db-snapshot-identifier "$ID" --tags Key=projeto,Value=nautam Key=motivo,Value=pre-migracao >/dev/null
  aws rds wait db-snapshot-available --region "$AWS_REGION" --db-snapshot-identifier "$ID"
  echo "Snapshot disponível."
  saida "$ID"
else
  saida "nenhum"
fi
