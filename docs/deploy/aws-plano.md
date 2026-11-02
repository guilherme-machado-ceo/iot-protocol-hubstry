# Plano de implantação do Nautam IoT Protocol na AWS

Versão 2, de 02/11/2026. Incorpora a auditoria técnica da Luna (ChatGPT) sobre a versão 1.

Status: a Etapa 1 está em revisão por pull request. Nenhum recurso foi criado na AWS (Amazon Web Services).

## 1. Governança

O Claude planeja, implementa e revisa. A Luna faz a auditoria técnica independente. O Guilherme Machado decide e aprova cada merge e cada etapa de infraestrutura. Divergências entre os agentes são registradas com fundamento, sem aprovação automática entre eles.

## 2. Fonte da verdade e destinos

A branch `main` do repositório `guilherme-machado-ceo/iot-protocol-hubstry` é a única fonte da verdade. A branch `master` foi consolidada na `main` e será apagada depois que a Vercel e o Streamlit Community Cloud passarem a publicar a partir da `main`.

| Peça | Destino atual | Destino AWS | Situação |
|---|---|---|---|
| Frontend Next.js (`demo-web/harmonic-demo`) | Vercel, projeto `iot-protocol-hubstry` | AWS Amplify Hosting | Amplify vira canônico após homologação |
| API Fastify (`server/`) | Nenhum | Amazon ECS Express Mode | Nova |
| Dashboard Streamlit (`dashboard.py`) | Streamlit Community Cloud | Amazon ECS Express Mode | Opcional, com aprovação de custo própria |
| Banco PostgreSQL | Nenhum | Amazon RDS for PostgreSQL | Novo, privado |

O ECS (Elastic Container Service, serviço de contêineres elásticos) executa as imagens. O Express Mode cria automaticamente o serviço sobre Fargate, o balanceador de carga e o HTTPS. O App Runner foi descartado porque a AWS encerrou a aceitação de novos clientes em 30/04/2026.

A Vercel não deve ser tratada como espelho comercial se o time estiver no plano Hobby, cujos termos restringem o uso a fins pessoais e não comerciais. O plano contratado precisa ser confirmado antes de qualquer uso comercial.

## 3. Decisões da auditoria

| Tema | Decisão | Fundamento |
|---|---|---|
| Região | `sa-east-1` (São Paulo) | Latência menor para o público brasileiro e residência dos dados no país. A residência ajuda na estratégia de LGPD (Lei Geral de Proteção de Dados), mas não comprova conformidade por si só. |
| Orquestração | ECS Express Mode | Menos configuração para o piloto. O ECS Fargate clássico fica como alternativa caso se exija contêineres em sub-redes privadas. |
| Banco | RDS PostgreSQL `db.t4g.micro`, Single-AZ | Simples e previsível. O Aurora Serverless v2 só pausa sem conexões abertas, o que o pool do Prisma pode impedir. |
| Domínio canônico | AWS, após testes de aceitação | Prepara a integração futura com o AWS IoT Core. |
| AWS e GCP | Convivência seletiva | A AWS hospeda a produção do Nautam. A GCP (Google Cloud Platform) fica para pesquisa e outros produtos, sem duplicar API, banco ou frontend de produção. |

## 4. Modelo de rede

O Express Mode atribui IP público às tarefas quando usa sub-redes públicas. Em sub-redes privadas, ele cria apenas um balanceador interno. O piloto adota sub-redes públicas, com as seguintes restrições:

- O ALB (Application Load Balancer, balanceador de aplicação) recebe tráfego da internet nas portas 80 e 443.
- O security group das tarefas aceita entrada somente do security group do ALB, nas portas 3001 (API) e 8501 (dashboard).
- O security group do RDS aceita a porta 5432 somente dos security groups da API e da tarefa de migração.
- O RDS não tem acesso público.
- Não há NAT Gateway, porque ele acrescentaria um custo fixo desnecessário ao piloto. As tarefas alcançam o ECR (Elastic Container Registry) e o Secrets Manager pelo próprio IP público.

Se a política de segurança exigir tarefas sem IP público, a migração para ECS Fargate clássico com sub-redes privadas exigirá NAT Gateway ou VPC endpoints, com o custo correspondente reavaliado.

## 5. Verificações de saúde

| Serviço | Porta | Liveness | Readiness (health check do ALB) |
|---|---|---|---|
| API Fastify | 3001 | `/api/livez` | `/api/readyz` (503 quando o banco cai) |
| Dashboard Streamlit | 8501 | — | `/_stcore/health` |

As dependências diretas do dashboard estão fixadas em `requirements.txt`, que o Streamlit Community Cloud também usa. As transitivas da imagem Docker estão em `constraints-dashboard.txt`.

O endpoint legado `/api/health` foi mantido por compatibilidade e passou a responder 503 quando o banco está indisponível.

## 5.1 Autenticação da API

Nenhuma rota de dados fica aberta. As rotas de saúde (`/api/livez`, `/api/readyz`, `/api/health`, `/api/metrics`) e a documentação (`/docs`) dispensam credencial; todas as demais exigem uma chave de API com o escopo correspondente.

| Rota | Escopo |
|---|---|
| `POST /api/devices/register` | `devices:write` |
| `GET /api/devices`, `GET /api/devices/:deviceId` | `devices:read` |
| `POST /api/harmonic/simulate` | `harmonic:write` |
| `GET /api/harmonic/hn`, `GET /api/harmonic/channels`, `POST /api/harmonic/fft` | `harmonic:compute` |

As rotas harmônicas seguem o contrato do núcleo Python: razões a/b do conjunto H16 (159 razões irredutíveis com a, b ≤ 16) e canais do HPM 1.0, em `server/src/protocol/h16.ts`. A equivalência com `hpg_core` é verificada no CI por fixtures regeneradas a partir do próprio Python. A única diferença deliberada: a API recusa componentes acima da frequência de Nyquist, que o núcleo Python decodificaria com aliasing.

A chave segue o formato `nk_<prefixo>_<segredo>` e é enviada no cabeçalho `x-api-key` ou em `Authorization: Bearer`. O banco guarda só o prefixo e o SHA-256 da chave; a chave em claro aparece uma única vez, na criação. Cada chave tem escopos, expiração opcional e revogação. A gestão é feita pelo comando `npm run apikey -- create | list | revoke`. Em produção, ele roda como tarefa avulsa do ECS com a imagem da API, porque o banco é privado.

Em produção, a chave criada nunca vai para a saída padrão, porque tudo o que a tarefa imprime fica no CloudWatch Logs. O comando exige `--secret-name /nautam/production/apikeys/<nome>`, grava a chave num segredo novo do Secrets Manager e imprime só o ARN (Amazon Resource Name, identificador do recurso) do segredo. Se a gravação falhar, a chave recém-criada é revogada, para não restar chave ativa irrecuperável. A opção `--stdout` existe só para desenvolvimento local e CI e falha fechada: é aceita apenas com `NODE_ENV=test` ou `development`, e qualquer outro valor, inclusive variável ausente, recusa. Quem precisa entregar a chave a um parceiro a lê com `aws secretsmanager get-secret-value --secret-id <ARN>`.

A tarefa do CLI usa um papel IAM próprio, separado do papel da API, com `secretsmanager:CreateSecret` e `secretsmanager:TagResource` restritos a `arn:aws:secretsmanager:<região>:<conta>:secret:/nautam/production/apikeys/*`. A API em execução não ganha permissão de criar segredos.

O HSL é parte do protocolo e não substitui a autenticação da API. A identidade de dispositivos reais fica para a Etapa 6, com o AWS IoT Core.

## 6. Migrações do banco

A migração inicial foi versionada em `server/prisma/migrations/`. Ela roda numa tarefa avulsa do ECS dentro da VPC (Virtual Private Cloud, rede privada virtual), e nunca a partir do runner do GitHub, porque o RDS é privado. A sequência de cada deploy é:

1. Construir e publicar as imagens no ECR.
2. Executar a tarefa `nautam-migrate`, que roda `prisma migrate deploy`.
3. Validar o resultado com `deploy/aws/run-migration.sh`: falhas de agendamento, ausência da tarefa ou do container `migrate`, `stopCode`, `stoppedReason` e `exitCode`. Qualquer falha interrompe o deploy e exibe os logs do CloudWatch.
4. Atualizar o serviço da API.
5. Testar `/api/readyz` no endereço público.

As migrações não rodam na inicialização de cada réplica da API.

## 7. Identidade do GitHub na AWS (OIDC)

O workflow assume um papel IAM (Identity and Access Management) por OIDC (OpenID Connect), sem chave estática. O job de deploy usa o Environment `production` do GitHub, com aprovação obrigatória e restrito à branch `main`. Com Environment, o campo `sub` do token muda de formato, e a política de confiança precisa refletir exatamente esse formato.

Política de confiança proposta:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:guilherme-machado-ceo/iot-protocol-hubstry:environment:production"
        }
      }
    }
  ]
}
```

Antes de criar o papel, é preciso conferir o `sub` real de um token deste repositório. Repositórios criados após 15/07/2026, ou que adotaram identificadores imutáveis, podem emitir `sub` com os IDs numéricos do proprietário e do repositório.

As permissões do papel ficam restritas a:

- `ecr:GetAuthorizationToken` e push e pull somente nos repositórios `nautam/*`;
- `ecs:RegisterTaskDefinition`, `ecs:RunTask`, `ecs:DescribeTasks` e as ações do Express Mode somente no cluster do Nautam;
- `iam:PassRole` somente para os papéis de execução, de tarefa e de infraestrutura do ECS do Nautam;
- `rds:CreateDBSnapshot`, `rds:AddTagsToResource` e `rds:DescribeDBSnapshots` somente na instância do Nautam;
- `ssm:GetParameter` e `ssm:PutParameter` somente no parâmetro `/nautam/production/ultimo-deploy`.

## 8. Custos

Nenhum recurso é criado antes da estimativa mensal. O script `deploy/aws/estimar_custos.py` consulta a AWS Price List API, que é gratuita e somente de leitura. Ele compara `sa-east-1` e `us-east-1`, com 730 horas por mês, e tem a opção de incluir o dashboard. Deve rodar no AWS CloudShell:

```bash
python3 deploy/aws/estimar_custos.py
python3 deploy/aws/estimar_custos.py --com-dashboard --detalhes
```

O script falha em vez de escolher um preço quando um item tem mais de um preço possível ou uma unidade inesperada. A opção `--detalhes` imprime o `usagetype`, a unidade e a descrição de cada preço usado. Essa saída serve de evidência para a revisão, e nenhuma estimativa autoriza gasto sem ela.

O script cobre Fargate, ALB, IPv4 públicos, RDS, armazenamento gp3, Secrets Manager, CloudWatch Logs e ECR. Amplify e transferência de dados dependem do uso e ficam listados à parte.

Controles adotados:

- alerta no AWS Budgets para gasto real e projetado (alerta não é teto de gasto);
- retenção de 14 dias nos grupos de log do CloudWatch;
- política de ciclo de vida no ECR, mantendo as 10 imagens mais recentes.

## 9. Backup e reversão

- Backup automatizado do RDS com retenção de 7 dias.
- Proteção contra exclusão ativada no RDS.
- Snapshot final obrigatório antes de qualquer exclusão do banco.
- Snapshot pré-migração condicionado ao risco (`deploy/aws/snapshot-se-arriscado.sh`): o deploy compara as migrações com o último commit implantado, registrado no SSM Parameter Store. Só tira snapshot se houver operação destrutiva ou que reescreve dados (`DROP` de tabela, coluna, esquema, tipo, índice ou restrição; `TRUNCATE`; `DELETE`; `UPDATE` com ou sem aspas; mudança de tipo; `SET NOT NULL`; renomeação). Migrações só aditivas seguem sem snapshot. O disparo manual aceita `auto`, `sempre` ou `nunca`. O script falha fechado: só a ausência do parâmetro (`ParameterNotFound`) conta como primeiro deploy, e acesso negado ou falha de rede ao ler o SSM interrompem o deploy. Migração já aplicada que tenha sido alterada, removida ou renomeada também interrompe. Os casos são testados no CI por `deploy/aws/testes/testar-snapshot.sh`, com um `aws` simulado.
- Serviços ECS, Amplify e workflow podem ser desligados isoladamente, sem afetar Vercel e Streamlit Cloud.
- O banco é o único componente cuja exclusão destrói dados, e por isso só é removido depois do snapshot final.

## 10. Etapas e critérios de avanço

| Etapa | Trabalho | Critério para avançar |
|---|---|---|
| 0 | Consolidar `master` na `main`; trocar a branch da Vercel e do Streamlit; apagar `master` | `main` como única fonte da verdade |
| 1 | Dockerfiles, lockfile, migração, correções da API, `amplify.yml`, workflows | PR aprovado; CI verde (build, migração sem drift, smoke tests) |
| 2 | Budgets, provedor OIDC, papéis IAM, ECR | Estimativa de custo aprovada; permissões auditadas |
| 3 | RDS e migração inicial | Banco privado, migração validada, backup ativo |
| 4 | API no ECS e frontend no Amplify | Testes funcionais e de disponibilidade |
| 4.1 | Dashboard no ECS | Aprovação específica de custo |
| 5 | Domínios na Cloudflare | HTTPS, DNS e aceitação pública |
| 6 | AWS IoT Core | Projeto e auditoria próprios |

A Etapa 1 só cria arquivos no repositório. O workflow `deploy-aws.yml` tem apenas disparo manual e depende de variáveis do Environment `production` que ainda não existem.

## 11. Condições para a Etapa 6 (AWS IoT Core)

A integração com o AWS IoT Core exigirá projeto e auditoria próprios, cobrindo:

- identidade individual de cada dispositivo;
- certificados X.509 com autenticação TLS mútua;
- políticas de autorização por dispositivo e por tópico MQTT;
- provisionamento, rotação e revogação de certificados;
- monitoramento e resposta a dispositivos comprometidos.

O HSL e a rotação de chaves por LFSR (Linear Feedback Shift Register) do protocolo não substituem esses mecanismos de identidade e autorização.

## 12. Variáveis do Environment `production` (Etapa 2)

| Variável | Exemplo |
|---|---|
| `AWS_REGION` | `sa-east-1` |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::<ACCOUNT_ID>:role/nautam-github-deploy` |
| `ECR_API_REPO` | `nautam/api` |
| `ECR_DASHBOARD_REPO` | `nautam/dashboard` |
| `ECS_CLUSTER` | `nautam` |
| `ECS_API_SERVICE` | `nautam-api` |
| `ECS_DASHBOARD_SERVICE` | `nautam-dashboard` |
| `ECS_EXECUTION_ROLE_ARN` | papel de execução das tarefas |
| `ECS_TASK_ROLE_ARN` | papel da aplicação |
| `ECS_INFRASTRUCTURE_ROLE_ARN` | papel de infraestrutura do Express Mode |
| `ECS_SUBNETS` | `subnet-...,subnet-...` |
| `ECS_API_SECURITY_GROUPS` | security group da API |
| `ECS_DASHBOARD_SECURITY_GROUPS` | security group do dashboard |
| `ECS_MIGRATE_SECURITY_GROUPS` | security group da migração |
| `DATABASE_URL_SECRET_ARN` | ARN do segredo no Secrets Manager |
| `DB_INSTANCE_ID` | identificador da instância RDS, para o snapshot pré-migração |
| `CORS_ORIGIN` | domínio canônico do frontend |
| `API_BASE_URL` | URL pública da API |

Nenhum valor secreto fica no GitHub. O `DATABASE_URL` é lido do Secrets Manager pelas próprias tarefas.
