#!/usr/bin/env bash
# Testa deploy/aws/snapshot-se-arriscado.sh com um "aws" simulado e um
# repositório git temporário. Rodar da raiz: bash deploy/aws/testes/testar-snapshot.sh
set -uo pipefail
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/snapshot-se-arriscado.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/repo/server/prisma/migrations/001_init"
cat > "$T/bin/aws" <<'FAKE'
#!/usr/bin/env bash
case "$1 $2" in
 "ssm get-parameter") case "$SSM" in
   ok) cat "$SHA_FILE";;
   notfound) echo "An error occurred (ParameterNotFound) when calling the GetParameter operation" >&2; exit 254;;
   denied) echo "An error occurred (AccessDeniedException) when calling the GetParameter operation" >&2; exit 254;;
   rede) echo "Could not connect to the endpoint URL" >&2; exit 255;; esac;;
 "rds create-db-snapshot") echo "SNAPSHOT_CRIADO";;
 "rds wait") :;;
esac
FAKE
chmod +x "$T/bin/aws"
cd "$T/repo" && git init -q && git config user.email t@t && git config user.name t
M=server/prisma/migrations
printf 'CREATE TABLE "A" (id int, b int REFERENCES "B"(id) ON UPDATE CASCADE);\n' > $M/001_init/migration.sql
git add -A && git commit -qm init && git rev-parse HEAD > "$T/sha"

FALHAS=0
caso() { # caso <nome> <SSM> <rc esperado> <texto esperado>   (MODO via variável, padrão auto)
  local out rc
  out=$(PATH="$T/bin:$PATH" SHA_FILE="$T/sha" SSM="$2" MODO="${MODO:-auto}" DB_INSTANCE_ID=db AWS_REGION=sa-east-1 \
        PARAM_ULTIMO_DEPLOY=/nautam/production/ultimo-deploy bash "$SCRIPT" 2>&1); rc=$?
  if [ "$rc" = "$3" ] && grep -q -- "$4" <<<"$out"; then echo "ok   $1"
  else echo "FALHA $1 (rc=$rc, esperado $3; procurado '$4')"; echo "$out" | sed 's/^/     /'; FALHAS=$((FALHAS+1)); fi
}
novo() { mkdir -p "$M/$1"; printf '%s\n' "$2" > "$M/$1/migration.sql"; git add -A; git commit -qm "$1"; }

caso "primeiro deploy (ParameterNotFound)" notfound 0 "snapshot=nenhum"
caso "SSM com acesso negado interrompe"     denied   1 "deploy interrompido"
caso "SSM sem rede interrompe"              rede     1 "deploy interrompido"
caso "sem migração nova"                    ok       0 "snapshot=nenhum"
novo 002_add 'ALTER TABLE "A" ADD COLUMN c int;'
caso "aditiva; ON UPDATE CASCADE não conta" ok       0 "só aditivas"
novo 003_upd 'update A set c = 1;'
caso "UPDATE sem aspas tira snapshot"       ok       0 "snapshot=db-pre-migracao"
git reset -q --hard HEAD~1
novo 003_nn 'ALTER TABLE "A" ALTER COLUMN "c" SET NOT NULL;'
caso "SET NOT NULL tira snapshot"           ok       0 "snapshot=db-pre-migracao"
git reset -q --hard HEAD~1
novo 003_di 'DROP INDEX "A_c_idx";'
caso "DROP INDEX tira snapshot"             ok       0 "snapshot=db-pre-migracao"
git reset -q --hard HEAD~1
novo 003_dc 'ALTER TABLE "A" DROP CONSTRAINT "A_b_fkey";'
caso "DROP CONSTRAINT tira snapshot"        ok       0 "snapshot=db-pre-migracao"
git reset -q --hard HEAD~2
echo '-- editada' >> $M/001_init/migration.sql; git commit -qam edit
caso "migração aplicada alterada"           ok       1 "deploy interrompido"
MODO=sempre caso "alterada, modo sempre não contorna" ok 1 "deploy interrompido"
MODO=nunca  caso "alterada, modo nunca não contorna"  ok 1 "deploy interrompido"
git reset -q --hard HEAD~1; git mv $M/001_init $M/001_x; git commit -qm mv
caso "migração aplicada renomeada"          ok       1 "deploy interrompido"
git reset -q --hard HEAD~1; git rm -rq $M/001_init; git commit -qm rm
caso "migração aplicada removida"           ok       1 "deploy interrompido"
MODO=nunca  caso "removida, modo nunca não contorna"   ok 1 "deploy interrompido"
git reset -q --hard HEAD~1
MODO=sempre caso "modo sempre sem alteração tira snapshot" ok 0 "snapshot=db-pre-migracao"
MODO=nunca  caso "modo nunca sem alteração dispensa"       ok 0 "snapshot=nenhum"
MODO=xyz    caso "modo inválido"                           ok 2 "MODO inválido"
echo deadbeefdeadbeefdeadbeefdeadbeefdeadbeef > "$T/sha"
caso "último deploy fora do histórico interrompe"         ok 1 "não está no histórico"

[ "$FALHAS" -eq 0 ] && echo "Todos os casos passaram." || { echo "$FALHAS caso(s) falharam."; exit 1; }
