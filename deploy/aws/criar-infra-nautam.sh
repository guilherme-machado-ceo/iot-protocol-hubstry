#!/usr/bin/env bash
# Cria, de forma idempotente, tudo o que o workflow "Deploy AWS" precisa para a
# API do Nautam, na VPC padrão de sa-east-1. Rodar no CloudShell como admin-solo:
#   bash criar-infra-nautam.sh
# Sem "set -e" (fecharia o CloudShell); cada passo checa e para no primeiro erro.
# Nenhum segredo é impresso: a senha do banco é gerada aqui e vai direto para o
# Secrets Manager. Custo estimado: ~US$ 55/mês (RDS micro + 1 tarefa Fargate + ALB).

export AWS_PAGER="" AWS_REGION=sa-east-1 AWS_DEFAULT_REGION=sa-east-1
REPO="guilherme-machado-ceo/iot-protocol-hubstry"
ACC=$(aws sts get-caller-identity --query Account --output text) || { echo "sem credenciais"; exit 1; }
TAGS='Key=projeto,Value=nautam Key=ambiente,Value=production Key=responsavel,Value=guilherme'
para() { echo; echo "PAROU: $1"; exit 1; }
ok() { echo "  ok: $1"; }
existe_papel() { aws iam get-role --role-name "$1" >/dev/null 2>&1; }

echo "== 1. Rede: VPC padrão e sub-redes públicas"
VPC=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
[ -n "$VPC" ] && [ "$VPC" != "None" ] || para "a conta não tem VPC padrão em sa-east-1"
CIDR=$(aws ec2 describe-vpcs --vpc-ids "$VPC" --query 'Vpcs[0].CidrBlock' --output text)
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC" Name=default-for-az,Values=true --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
[ -n "$SUBNETS" ] || para "VPC padrão sem sub-redes padrão"
ok "VPC $VPC ($CIDR), sub-redes $SUBNETS"

echo "== 2. Security groups"
sg() { # sg <nome> <descrição>
  local id
  id=$(aws ec2 describe-security-groups --filters Name=vpc-id,Values="$VPC" Name=group-name,Values="$1" --query 'SecurityGroups[0].GroupId' --output text)
  if [ -z "$id" ] || [ "$id" = "None" ]; then
    id=$(aws ec2 create-security-group --vpc-id "$VPC" --group-name "$1" --description "$2" \
      --tag-specifications "ResourceType=security-group,Tags=[{Key=projeto,Value=nautam},{Key=Name,Value=$1}]" --query GroupId --output text) || return 1
  fi
  echo "$id"
}
SG_TASKS=$(sg nautam-tasks "Tarefas da API e da migracao do Nautam") || para "criar SG das tarefas"
SG_DB=$(sg nautam-db "PostgreSQL do Nautam, so a partir das tarefas") || para "criar SG do banco"
# Tarefas: entrada só na porta 3001, de dentro da VPC (onde fica o balanceador).
aws ec2 authorize-security-group-ingress --group-id "$SG_TASKS" --protocol tcp --port 3001 --cidr "$CIDR" >/dev/null 2>&1
# Banco: entrada só na 5432, só do SG das tarefas.
aws ec2 authorize-security-group-ingress --group-id "$SG_DB" --protocol tcp --port 5432 --source-group "$SG_TASKS" >/dev/null 2>&1
ok "tarefas $SG_TASKS, banco $SG_DB"

echo "== 3. ECR"
for r in nautam/api; do
  aws ecr describe-repositories --repository-names "$r" >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name "$r" --image-scanning-configuration scanOnPush=true --tags Key=projeto,Value=nautam >/dev/null || para "criar ECR $r"
  aws ecr put-lifecycle-policy --repository-name "$r" --lifecycle-policy-text \
    '{"rules":[{"rulePriority":1,"description":"manter 20","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":20},"action":{"type":"expire"}}]}' >/dev/null
done
ok "nautam/api"

echo "== 4. Banco PostgreSQL (RDS db.t4g.micro, privado, backup 7 dias)"
DB_ID=nautam-db
if ! aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  SENHA=$(openssl rand -hex 24)
  aws rds create-db-instance --db-instance-identifier "$DB_ID" --engine postgres --engine-version 16 \
    --db-instance-class db.t4g.micro --allocated-storage 20 --storage-type gp3 \
    --master-username nautam --master-user-password "$SENHA" --db-name nautam \
    --vpc-security-group-ids "$SG_DB" --no-publicly-accessible --backup-retention-period 7 \
    --storage-encrypted --deletion-protection --no-multi-az --tags $TAGS >/dev/null || para "criar RDS"
  echo "  criando o banco (5 a 10 minutos)..."
  aws rds wait db-instance-available --db-instance-identifier "$DB_ID" || para "esperar o RDS"
  HOST=$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" --query 'DBInstances[0].Endpoint.Address' --output text)
  URL="postgresql://nautam:${SENHA}@${HOST}:5432/nautam?schema=public&sslmode=require"
  if aws secretsmanager describe-secret --secret-id /nautam/production/database-url >/dev/null 2>&1; then
    aws secretsmanager put-secret-value --secret-id /nautam/production/database-url --secret-string "$URL" >/dev/null || para "atualizar segredo"
  else
    aws secretsmanager create-secret --name /nautam/production/database-url --secret-string "$URL" \
      --tags Key=projeto,Value=nautam >/dev/null || para "criar segredo"
  fi
  unset SENHA URL
else
  aws rds wait db-instance-available --db-instance-identifier "$DB_ID" || para "esperar o RDS"
  aws secretsmanager describe-secret --secret-id /nautam/production/database-url >/dev/null 2>&1 \
    || para "RDS existe mas o segredo /nautam/production/database-url não; não dá para recuperar a senha"
fi
SECRET_ARN=$(aws secretsmanager describe-secret --secret-id /nautam/production/database-url --query ARN --output text)
ok "banco $DB_ID e segredo $SECRET_ARN"

echo "== 5. Papéis do ECS"
CONF_TAREFA='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
existe_papel nautam-ecs-execution || aws iam create-role --role-name nautam-ecs-execution --assume-role-policy-document "$CONF_TAREFA" >/dev/null || para "papel de execução"
aws iam attach-role-policy --role-name nautam-ecs-execution --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy || para "política de execução"
aws iam put-role-policy --role-name nautam-ecs-execution --policy-name segredo-e-logs --policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"'"$SECRET_ARN"'"},{"Effect":"Allow","Action":"logs:CreateLogGroup","Resource":"*"}]}' || para "política inline de execução"
existe_papel nautam-ecs-task || aws iam create-role --role-name nautam-ecs-task --assume-role-policy-document "$CONF_TAREFA" >/dev/null || para "papel de tarefa"
existe_papel nautam-ecs-infra || aws iam create-role --role-name nautam-ecs-infra --assume-role-policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null || para "papel de infraestrutura"
aws iam attach-role-policy --role-name nautam-ecs-infra --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices || para "política de infraestrutura"
# Papéis vinculados a serviço do ECS e do balanceador; já existir não é erro.
for svc in ecs.amazonaws.com elasticloadbalancing.amazonaws.com; do
  aws iam create-service-linked-role --aws-service-name "$svc" >/dev/null 2>&1 || true
done
aws ecs create-cluster --cluster-name default >/dev/null || para "cluster default"
ok "execução, tarefa, infraestrutura e cluster default"

echo "== 6. GitHub OIDC e papel de deploy"
OIDC_ARN="arn:aws:iam::$ACC:oidc-provider/token.actions.githubusercontent.com"
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" >/dev/null 2>&1 || \
  aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com --client-id-list sts.amazonaws.com >/dev/null || para "provedor OIDC"
CONF_GH='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Federated":"'"$OIDC_ARN"'"},"Action":"sts:AssumeRoleWithWebIdentity","Condition":{"StringEquals":{"token.actions.githubusercontent.com:aud":"sts.amazonaws.com","token.actions.githubusercontent.com:sub":"repo:'"$REPO"':environment:production"}}}]}'
if existe_papel nautam-github-deploy; then
  aws iam update-assume-role-policy --role-name nautam-github-deploy --policy-document "$CONF_GH" || para "confiança do deploy"
else
  aws iam create-role --role-name nautam-github-deploy --assume-role-policy-document "$CONF_GH" >/dev/null || para "papel de deploy"
fi
R="arn:aws:iam::$ACC:role"
aws iam put-role-policy --role-name nautam-github-deploy --policy-name deploy-nautam --policy-document '{
 "Version":"2012-10-17","Statement":[
  {"Effect":"Allow","Action":"ecr:GetAuthorizationToken","Resource":"*"},
  {"Effect":"Allow","Action":["ecr:BatchCheckLayerAvailability","ecr:InitiateLayerUpload","ecr:UploadLayerPart","ecr:CompleteLayerUpload","ecr:PutImage","ecr:BatchGetImage","ecr:GetDownloadUrlForLayer","ecr:DescribeImages"],"Resource":"arn:aws:ecr:sa-east-1:'"$ACC"':repository/nautam/*"},
  {"Effect":"Allow","Action":["ecs:*","elasticloadbalancing:Describe*","ec2:Describe*","acm:DescribeCertificate","acm:ListCertificates","logs:GetLogEvents","logs:DescribeLogStreams"],"Resource":"*"},
  {"Effect":"Allow","Action":"iam:PassRole","Resource":["'"$R"'/nautam-ecs-execution","'"$R"'/nautam-ecs-task","'"$R"'/nautam-ecs-infra"]},
  {"Effect":"Allow","Action":["ssm:GetParameter","ssm:PutParameter"],"Resource":"arn:aws:ssm:sa-east-1:'"$ACC"':parameter/nautam/production/*"},
  {"Effect":"Allow","Action":["rds:CreateDBSnapshot","rds:AddTagsToResource","rds:DescribeDBSnapshots"],"Resource":["arn:aws:rds:sa-east-1:'"$ACC"':db:nautam-db","arn:aws:rds:sa-east-1:'"$ACC"':snapshot:nautam-db-*"]}
 ]}' || para "permissões do deploy"
ok "OIDC e nautam-github-deploy"

echo
echo "== PRONTO. Cole no chat a linha abaixo (só identificadores, nenhum segredo):"
printf 'VARS AWS_REGION=sa-east-1 ECR_API_REPO=nautam/api ECR_DASHBOARD_REPO=nautam/dashboard ECS_CLUSTER=default ECS_API_SERVICE=nautam-api ECS_DASHBOARD_SERVICE=nautam-dashboard DB_INSTANCE_ID=%s AWS_DEPLOY_ROLE_ARN=%s ECS_EXECUTION_ROLE_ARN=%s ECS_TASK_ROLE_ARN=%s ECS_INFRASTRUCTURE_ROLE_ARN=%s DATABASE_URL_SECRET_ARN=%s ECS_SUBNETS=%s ECS_API_SECURITY_GROUPS=%s ECS_MIGRATE_SECURITY_GROUPS=%s ECS_DASHBOARD_SECURITY_GROUPS=%s\n' \
  "$DB_ID" "$R/nautam-github-deploy" "$R/nautam-ecs-execution" "$R/nautam-ecs-task" "$R/nautam-ecs-infra" "$SECRET_ARN" "$SUBNETS" "$SG_TASKS" "$SG_TASKS" "$SG_TASKS"
