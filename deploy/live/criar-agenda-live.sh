#!/usr/bin/env bash
# Nautam Live — tarefa 4 (E1): permissões e agenda do job de ingestão.
# Idempotente. Rodar no CloudShell como admin-solo:  bash criar-agenda-live.sh
# Cria a agenda DESLIGADA. Ligar só depois do teste manual:  bash criar-agenda-live.sh ligar
export AWS_PAGER="" AWS_REGION=sa-east-1
ACC=$(aws sts get-caller-identity --query Account --output text) || { echo "sem credenciais"; exit 1; }
para() { echo "PAROU: $1"; exit 1; }
R="arn:aws:iam::$ACC:role"
DB_SECRET=$(aws secretsmanager describe-secret --secret-id /nautam/production/database-url --query ARN --output text) || para "segredo do banco"
OAQ_SECRET=$(aws secretsmanager describe-secret --secret-id /nautam/production/openaq-api-key --query ARN --output text) || para "segredo da OpenAQ"
SUBNETS=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true --query 'Subnets[].SubnetId' --output json) || para "sub-redes"
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=nautam-tasks --query 'SecurityGroups[0].GroupId' --output text)
[ -n "$SG" ] && [ "$SG" != "None" ] || para "SG nautam-tasks não encontrado"

echo "== 1. Papel de execução lê também a chave da OpenAQ"
aws iam put-role-policy --role-name nautam-ecs-execution --policy-name segredo-e-logs --policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":["'"$DB_SECRET"'","'"$OAQ_SECRET"'"]},{"Effect":"Allow","Action":"logs:CreateLogGroup","Resource":"*"}]}' || para "política de execução"
echo "  ok"

echo "== 2. Papel do EventBridge Scheduler"
aws iam get-role --role-name nautam-live-scheduler >/dev/null 2>&1 || \
  aws iam create-role --role-name nautam-live-scheduler --assume-role-policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"scheduler.amazonaws.com"},"Action":"sts:AssumeRole","Condition":{"StringEquals":{"aws:SourceAccount":"'"$ACC"'"}}}]}' >/dev/null || para "papel do scheduler"
aws iam put-role-policy --role-name nautam-live-scheduler --policy-name rodar-nautam-live --policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"ecs:RunTask","Resource":["arn:aws:ecs:sa-east-1:'"$ACC"':task-definition/nautam-live","arn:aws:ecs:sa-east-1:'"$ACC"':task-definition/nautam-live:*"]},{"Effect":"Allow","Action":"ecs:TagResource","Resource":"*"},{"Effect":"Allow","Action":"iam:PassRole","Resource":["'"$R"'/nautam-ecs-execution","'"$R"'/nautam-ecs-task"]}]}' || para "permissões do scheduler"
echo "  ok"

ESTADO=DISABLED; [ "${1:-}" = "ligar" ] && ESTADO=ENABLED
echo "== 3. Agenda nautam-live-production a cada 5 min (estado: $ESTADO)"
aws ecs describe-task-definition --task-definition nautam-live >/dev/null 2>&1 || para "task definition nautam-live ainda não existe: rode o Deploy AWS primeiro"
ALVO='{"Arn":"arn:aws:ecs:sa-east-1:'"$ACC"':cluster/default","RoleArn":"'"$R"'/nautam-live-scheduler","RetryPolicy":{"MaximumRetryAttempts":2,"MaximumEventAgeInSeconds":240},"EcsParameters":{"TaskDefinitionArn":"arn:aws:ecs:sa-east-1:'"$ACC"':task-definition/nautam-live","LaunchType":"FARGATE","TaskCount":1,"NetworkConfiguration":{"awsvpcConfiguration":{"Subnets":'"$SUBNETS"',"SecurityGroups":["'"$SG"'"],"AssignPublicIp":"ENABLED"}}}}'
if aws scheduler get-schedule --name nautam-live-production >/dev/null 2>&1; then
  aws scheduler update-schedule --name nautam-live-production --schedule-expression 'rate(5 minutes)' \
    --flexible-time-window Mode=OFF --state "$ESTADO" --target "$ALVO" >/dev/null || para "atualizar agenda"
else
  sleep 10  # propagação do papel recém-criado
  aws scheduler create-schedule --name nautam-live-production --schedule-expression 'rate(5 minutes)' \
    --flexible-time-window Mode=OFF --state "$ESTADO" --target "$ALVO" >/dev/null || para "criar agenda"
fi
aws scheduler get-schedule --name nautam-live-production \
  --query '{Estado:State,Expressao:ScheduleExpression,Tentativas:Target.RetryPolicy.MaximumRetryAttempts}' --output table

echo "== 4. Comando para o teste manual (uma execução agora):"
echo "aws ecs run-task --region sa-east-1 --cluster default --launch-type FARGATE --task-definition nautam-live --network-configuration 'awsvpcConfiguration={subnets=[$(echo "$SUBNETS" | jq -r 'join(",")')],securityGroups=[$SG],assignPublicIp=ENABLED}' --query 'tasks[0].taskArn' --output text"
echo "== 5. Resultado (depois de ~2 min):"
echo "aws logs tail /ecs/nautam-live --region sa-east-1 --since 10m --format short"
