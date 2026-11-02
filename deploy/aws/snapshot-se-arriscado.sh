#!/usr/bin/env bash
# Snapshot do RDS antes da migração, só quando ela for arriscada.
#
# Compara as migrações entre o último commit implantado com sucesso
# (guardado no SSM Parameter Store) e o commit atual. Se alguma migração
# nova contiver operação destrutiva ou que reescreve dados, tira um
# snapshot manual do RDS e espera ficar disponível antes de seguir.
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
PADRAO='DROP[[:space:]]+(TABLE|COLUMN|SCHEMA|TYPE)|TRUNCATE|DELETE[[:space:]]+FROM|UPDATE[[:space:]]+"|ALTER[[:space:]]+COLUMN[^;]*[[:space:]]TYPE|RENAME[[:space:]]+(COLUMN|TO)'

saida() {
  echo "snapshot=$1"
  if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "snapshot=$1" >> "$GITHUB_OUTPUT"; fi
}

decidir() {
  case "$MODO" in
    sempre) echo "Modo 'sempre'."; return 0 ;;
    nunca)  echo "Modo 'nunca'."; return 1 ;;
    auto)   ;;
    *) echo "::error::MODO inválido: $MODO"; exit 2 ;;
  esac

  ULTIMO=$(aws ssm get-parameter --name "$PARAM_ULTIMO_DEPLOY" --query Parameter.Value --output text 2>/dev/null || true)
  if [ -z "$ULTIMO" ] || [ "$ULTIMO" = "None" ]; then
    echo "Sem registro de deploy anterior (primeiro deploy): banco ainda vazio, snapshot dispensado."
    return 1
  fi
  if ! git cat-file -e "${ULTIMO}^{commit}" 2>/dev/null; then
    echo "::warning::Commit do último deploy ($ULTIMO) não está no histórico local; por segurança, tira snapshot."
    return 0
  fi

  NOVAS=$(git diff --name-only --diff-filter=AM "$ULTIMO" HEAD -- "$PASTA" | grep 'migration.sql$' || true)
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
