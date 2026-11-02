#!/usr/bin/env bash
# Executa "prisma migrate deploy" numa tarefa avulsa do ECS, dentro da VPC.
# Falha (exit != 0) em qualquer destes casos:
#   - run-task devolve "failures" ou nenhuma tarefa;
#   - a tarefa para sem o container "migrate";
#   - o container termina com exitCode diferente de 0 ou sem exitCode.
# Em caso de falha, mostra stopCode, stoppedReason, reason e os logs do CloudWatch.
#
# Variáveis obrigatórias:
#   ECS_CLUSTER, TASK_DEFINITION_ARN, SUBNETS (a,b), SECURITY_GROUPS (a,b), AWS_REGION
set -euo pipefail

: "${ECS_CLUSTER:?}" "${TASK_DEFINITION_ARN:?}" "${SUBNETS:?}" "${SECURITY_GROUPS:?}" "${AWS_REGION:?}"

CONTAINER_NAME="migrate"
LOG_GROUP="/ecs/nautam-migrate"
LOG_PREFIX="migrate"

show_logs() {
  local task_id="$1"
  echo "--- Logs do CloudWatch (${LOG_GROUP}) ---"
  aws logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "${LOG_PREFIX}/${CONTAINER_NAME}/${task_id}" \
    --limit 200 --query 'events[].message' --output text 2>/dev/null \
    || echo "(logs indisponíveis)"
}

RUN_JSON=$(aws ecs run-task \
  --cluster "$ECS_CLUSTER" \
  --launch-type FARGATE \
  --task-definition "$TASK_DEFINITION_ARN" \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SECURITY_GROUPS}],assignPublicIp=ENABLED}" \
  --output json)

FAILURES=$(jq '.failures | length' <<<"$RUN_JSON")
if [ "$FAILURES" != "0" ]; then
  echo "::error::run-task devolveu falhas de agendamento:"
  jq -r '.failures[] | "  \(.arn // "-"): \(.reason // "-") \(.detail // "")"' <<<"$RUN_JSON"
  exit 1
fi

TASK_ARN=$(jq -r '.tasks[0].taskArn // empty' <<<"$RUN_JSON")
if [ -z "$TASK_ARN" ]; then
  echo "::error::run-task não devolveu nenhuma tarefa."
  exit 1
fi
TASK_ID="${TASK_ARN##*/}"
echo "Tarefa de migração: $TASK_ARN"

aws ecs wait tasks-stopped --cluster "$ECS_CLUSTER" --tasks "$TASK_ARN"

DESC=$(aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks "$TASK_ARN" --output json)
STOP_CODE=$(jq -r '.tasks[0].stopCode // "-"' <<<"$DESC")
STOPPED_REASON=$(jq -r '.tasks[0].stoppedReason // "-"' <<<"$DESC")
CONTAINER=$(jq -c --arg n "$CONTAINER_NAME" '.tasks[0].containers[]? | select(.name == $n)' <<<"$DESC")

if [ -z "$CONTAINER" ]; then
  echo "::error::Container '${CONTAINER_NAME}' não encontrado na tarefa. stopCode=${STOP_CODE} stoppedReason=${STOPPED_REASON}"
  show_logs "$TASK_ID"
  exit 1
fi

EXIT_CODE=$(jq -r '.exitCode // "ausente"' <<<"$CONTAINER")
REASON=$(jq -r '.reason // "-"' <<<"$CONTAINER")
echo "stopCode=${STOP_CODE} stoppedReason=${STOPPED_REASON} exitCode=${EXIT_CODE} reason=${REASON}"

if [ "$EXIT_CODE" != "0" ]; then
  echo "::error::A migração falhou (exitCode=${EXIT_CODE})."
  show_logs "$TASK_ID"
  exit 1
fi

echo "Migração concluída com sucesso."
