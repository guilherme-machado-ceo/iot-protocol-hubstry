#!/usr/bin/env bash
# Nautam Live — tarefa 1 (E1): qualifica as estações brasileiras da OpenAQ v3.
# Somente leitura. Rodar no CloudShell (sa-east-1) como admin-solo:
#   bash qualificar-openaq.sh
# Lê a chave do Secrets Manager e nunca a imprime. Não imprime coordenadas,
# nomes de contribuidores nem contatos. Critério de elegibilidade (fail-closed):
#   estação fixa (isMobile=false), monitor de referência (isMonitor=true),
#   leitura nas últimas 24 h e TODAS as licenças vigentes com
#   commercialUseAllowed=true e redistributionAllowed=true.

export AWS_PAGER="" AWS_REGION=sa-east-1
BASE=https://api.openaq.org/v3
K=$(aws secretsmanager get-secret-value --secret-id /nautam/production/openaq-api-key --query SecretString --output text) || { echo "PAROU: não li o segredo"; exit 1; }
K=$(printf '%s' "$K" | tr -d '[:space:]')
T=$(mktemp -d); trap 'rm -rf "$T"; unset K' EXIT

get() { # get <caminho> <arquivo>  -> imprime o código HTTP
  curl -s -o "$2" -D "$T/h" -w '%{http_code}' -H "X-API-Key: $K" -H 'Accept: application/json' "$BASE$1"
}

echo "== 1. Chave e limite de taxa"
C=$(get "/parameters?limit=1" "$T/p.json")
if [ "$C" != "200" ]; then
  echo "PAROU: OpenAQ respondeu HTTP $C. Se for 401, a chave gravada está errada (tamanho gravado: ${#K} caracteres)."
  exit 1
fi
grep -i '^x-ratelimit' "$T/h" | sed 's/^/  /' || true
echo "  ok: chave aceita (${#K} caracteres)"

echo "== 2. Estações no Brasil"
: > "$T/locs.jsonl"; P=1
while :; do
  C=$(get "/locations?iso=BR&limit=1000&page=$P" "$T/l.json")
  [ "$C" = "200" ] || { echo "PAROU: /locations HTTP $C"; exit 1; }
  jq -c '.results[]' "$T/l.json" >> "$T/locs.jsonl"
  N=$(jq '.results | length' "$T/l.json"); [ "$N" -lt 1000 ] && break; P=$((P+1)); sleep 1
done
TOTAL=$(wc -l < "$T/locs.jsonl")
echo "  encontradas: $TOTAL (meta.found da última página: $(jq '.meta.found' "$T/l.json"))"

echo "== 3. Licenças usadas por essas estações"
jq -r '.licenses[]?.id' "$T/locs.jsonl" | sort -un > "$T/lic_ids"
echo '{}' > "$T/lic.json"
while read -r id; do
  C=$(get "/licenses/$id" "$T/one.json")
  [ "$C" = "200" ] || { echo "  aviso: licença $id HTTP $C (tratada como inelegível)"; continue; }
  jq --arg id "$id" --slurpfile o "$T/one.json" '. + {($id): $o[0].results[0]}' "$T/lic.json" > "$T/lic2.json" && mv "$T/lic2.json" "$T/lic.json"
  sleep 0.5
done < "$T/lic_ids"
jq -r 'to_entries[] | "  licença \(.key): \(.value.name) | comercial=\(.value.commercialUseAllowed) redistribuição=\(.value.redistributionAllowed) atribuição=\(.value.attributionRequired) | \(.value.sourceUrl)"' "$T/lic.json"

echo "== 4. Elegíveis (fixa, monitor, ativa em 24 h, licença comercial + redistribuição)"
LIMITE=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
# Uma só regra de classificação, usada na lista e na contagem de exclusões.
CLASSE='def lics($L): [ .licenses[]? | select(.dateTo == null) | $L[(.id|tostring)] ];
  def classe($L; $lim):
    if .isMobile != false then "móvel"
    elif .isMonitor != true then "não é monitor de referência"
    elif (.datetimeLast.utc // "") < $lim then "sem leitura em 24 h"
    elif (lics($L)|length) == 0 then "sem licença vigente"
    elif all(lics($L)[]; . != null and .commercialUseAllowed == true and .redistributionAllowed == true) then "elegível"
    else "licença sem uso comercial ou redistribuição" end;'
jq -c --slurpfile L "$T/lic.json" --arg lim "$LIMITE" "$CLASSE"'
  select(classe($L[0]; $lim) == "elegível")
  | {id, provedor: .provider.name, proprietario: .owner.name, localidade: .locality,
     ultima: .datetimeLast.utc, licencas: [lics($L[0])[].name] | unique,
     parametros: [.sensors[].parameter.name] | unique}' "$T/locs.jsonl" > "$T/eleg.jsonl"
E=$(wc -l < "$T/eleg.jsonl")
echo "  elegíveis: $E de $TOTAL"
jq -r '"  \(.id) | \(.provedor) | \(.proprietario) | \(.localidade // "-") | última \(.ultima) | \(.licencas|join(", ")) | \(.parametros|join(","))"' "$T/eleg.jsonl" | head -40

echo "== 5. Classificação de todas as estações (contagem)"
jq -r --slurpfile L "$T/lic.json" --arg lim "$LIMITE" "$CLASSE"' classe($L[0]; $lim)' "$T/locs.jsonl" | sort | uniq -c | sort -rn | sed 's/^/  /'

echo
echo "== Cole a saída inteira no chat. eligible=$([ "$E" -gt 0 ] && echo true || echo false)"
