# Plano de Implementação — Nautam Live

> **Estado:** nenhuma tarefa autorizada ou executada. Cada tarefa exige aprovação explícita antes do início.
>
> **Limite de escopo:** nove tarefas em três entregas. Não criar hardware, broker MQTT, IoT Core, novo banco, NAT Gateway, novo ALB ou serviço permanente para o painel.

## E1 — Ingestão pública, persistência e agenda

- [ ] **1. Qualificar OpenAQ e ONS e congelar a configuração inicial**
  - Criar uma verificação somente de leitura para consultar `GET /v3/locations?iso=BR`, registrar `meta.found` e listar apenas estações fixas com proprietário institucional.
  - Consultar os metadados de licença e aceitar somente `commercialUseAllowed=true`, redistribuição permitida e atribuição preenchida.
  - Selecionar até 12 séries OpenAQ; configurar uma série pequena do bucket `s3://ons-aws-prod-opendata` como reserva.
  - Não persistir nem exibir coordenadas, nomes de contribuidores ou contatos.
  - Gerar um relatório versionado com endpoint, provedor, quantidade encontrada, licença, atribuição, cadência observada e timestamp da verificação.
  - **Critério verificável:** `npm run live:source-check -- --dry-run` encerra com código 0, imprime `eligible=true` para a fonte inicial e não imprime a chave; o relatório contém links de licença comercial e o comando `grep -Ei 'email|contributor|ownerName|latitude|longitude' docs/research/nautam-live-sources.md` não encontra campos pessoais/posição exata.
  - _Requisitos: 1.1–1.7, 8.3–8.5_

- [ ] **2. Criar a migração Prisma aditiva e a idempotência de dados**
  - Adicionar `LiveRun` e `LiveObservation` conforme o design, incluindo unicidade de `slotUtc` e de observação por provedor/sensor/parâmetro/instante.
  - Adicionar índices para execução, parâmetro e tempo sem modificar objetos existentes.
  - Manter a migração compatível com `prisma migrate deploy` na tarefa ECS existente.
  - **Critério verificável:** `npx prisma migrate diff --from-migrations prisma/migrations --to-schema-datamodel prisma/schema.prisma --shadow-database-url "$SHADOW_DATABASE_URL" --exit-code` retorna 0; `grep -Eiq 'DROP|TRUNCATE|DELETE FROM|ALTER .* TYPE|RENAME' server/prisma/migrations/*_nautam_live/migration.sql` retorna 1; após aplicar em banco limpo, `SELECT indexname FROM pg_indexes WHERE tablename IN ('LiveRun','LiveObservation');` mostra as restrições e índices especificados.
  - _Requisitos: 2.2–2.3, 3.1–3.6_

- [ ] **3. Implementar os adaptadores e o job de ingestão idempotente**
  - Implementar o contrato `LiveSourceAdapter` para OpenAQ e ONS.
  - Aplicar timeout, retries limitados, `Retry-After`, validação Zod, qualificação fail-closed e fallback.
  - Reivindicar o slot UTC numa transação, persistir observações novas e registrar `succeeded`, `failed` ou `no_new_data`.
  - Encerrar conexões Prisma em `finally`, usar logs estruturados e não registrar corpos externos completos ou segredos.
  - **Critério verificável:** duas execuções concorrentes com o mesmo `--slot` produzem uma única linha em `SELECT "slotUtc", count(*) FROM "LiveRun" GROUP BY "slotUtc" HAVING count(*) > 1;` (resultado vazio); `npm run live:run -- --source-fixture tests/fixtures/live-source.json --slot <UTC>` encerra em menos de quatro minutos e grava no máximo 12 observações.
  - _Requisitos: 1.4–1.6, 2.2–2.6, 3.3–3.5, 8.4–8.6_

- [ ] **4. Definir e preparar o agendamento ECS/Fargate lean**
  - Criar task definition que reutiliza a imagem `runtime`, sobrescreve o comando para o job, usa 0,25 vCPU/0,5 GB, log group próprio e os segredos estritamente necessários.
  - Criar papel do Scheduler com `ecs:RunTask` restrito e `iam:PassRole` apenas para os papéis da tarefa.
  - Estender o workflow existente para registrar a revisão e atualizar `nautam-live-production`, inicialmente `DISABLED`; habilitação só ocorre depois do smoke test aprovado.
  - Configurar `rate(5 minutes)`, janela flexível desligada, idade máxima de 240 segundos e duas tentativas.
  - **Critério verificável:** `aws scheduler get-schedule --name nautam-live-production --region sa-east-1 --query '{State:State,Expression:ScheduleExpression,Window:FlexibleTimeWindow.Mode,Retries:Target.RetryPolicy.MaximumRetryAttempts,Age:Target.RetryPolicy.MaximumEventAgeInSeconds}'` retorna `DISABLED`, `rate(5 minutes)`, `OFF`, `2`, `240`; `aws ecs describe-task-definition --task-definition nautam-live --query 'taskDefinition.{Cpu:cpu,Memory:memory,Command:containerDefinitions[0].command,Secrets:containerDefinitions[0].secrets[].name}'` mostra `256`, `512`, o comando do job e somente nomes esperados.
  - _Requisitos: 2.1, 2.6, 8.1–8.3, 8.7–8.8_

## E2 — Transmissão Nautam e métricas

- [ ] **5. Implementar normalização, composição H16 e ruído reproduzível**
  - Definir faixas e unidades por parâmetro, piso de amplitude e indicação de clipping.
  - Mapear deterministicamente até 12 observações para canais HPM 1.0.
  - Reutilizar `channelTable`, `compositeSignal` e `decodeFft`; não copiar o núcleo H16.
  - Adicionar AWGN com PRNG determinístico e persistir parâmetros, semente e SNR medido.
  - Calibrar amplitude por referência unitária processada pelo mesmo decoder.
  - **Critério verificável:** `npx vitest run tests/unit/live-signal.test.ts` demonstra que duas execuções com a mesma semente têm amostras/picos idênticos, que sementes diferentes alteram o ruído e que `f0=16384`, `sampleRate=131072`, `N=2048`; `SELECT "noiseSeed", "requestedSnrDb", "measuredSnrDb" FROM "LiveRun" ORDER BY id DESC LIMIT 1;` retorna valores preenchidos.
  - _Requisitos: 4.1–4.6_

- [ ] **6. Implementar métricas de detecção, sweep de SNR e canais vizinhos**
  - Calcular TP, FP, FN, precisão, recall/taxa de acerto, MAE de amplitude e tempo monotônico.
  - Aplicar correspondência por razão e erro de frequência máximo de `Δf/2`.
  - Executar uma vez por dia 20 sementes para cada SNR `[30,20,15,10,5,0,-5]` e publicar a menor SNR testada que cumpre os limiares.
  - Testar os três pares HPM mais próximos isoladamente e com todos os canais.
  - Rotular capacidade somente como valores/quadro, valores/segundo simulado, N amostras e tempo de CPU.
  - **Critério verificável:** `npm run live:benchmark -- --seed 1 --json` produz JSON com `trialsPerSnr=20`, sete SNRs, TP/FP/FN, precisão, recall, MAE, `minimumTestedSnrDb` ou `null`, e três pares com `separationHz`/`separationBins`; repetir o comando gera o mesmo JSON, exceto timestamps/tempo de CPU.
  - _Requisitos: 5.1–5.6_

- [ ] **7. Implementar a linha de base MQTT 3.1.1**
  - Serializar um payload canônico com exatamente as mesmas observações selecionadas.
  - Calcular PUBLISH QoS 0, PUBLISH QoS 1, PUBACK e Remaining Length em base 128.
  - Separar payload, overhead e total; informar exclusões de rede, broker, rádio e energia.
  - Não instalar nem executar broker MQTT.
  - **Critério verificável:** `npx vitest run tests/unit/mqtt-baseline.test.ts` valida fronteiras de Remaining Length em 127/128 e 16.383/16.384 bytes e confirma que QoS 1 adiciona Packet Identifier e PUBACK; `npm run live:mqtt-baseline -- --fixture tests/fixtures/live-source.json` mostra payload idêntico ao usado pelo run correspondente.
  - _Requisitos: 6.1–6.5, 9.4_

## E3 — API, painel e ativação controlada

- [ ] **8. Publicar API resumida e painel público na aplicação Fastify existente**
  - Implementar `/live`, `/api/live/public`, `/api/live/runs/:id` e o escopo administrativo previsto no design.
  - Limitar o endpoint público a janelas `24h`, `7d`, `30d`, uma série por consulta e no máximo 1.000 pontos agregados.
  - Mostrar estado normal/desatualizado/reserva/falha, valores, canais, métricas, baseline MQTT, origem, licença e instante observado.
  - Exibir literalmente “simulação de sinal com dados reais; energia e interferência em campo não medidas”.
  - Não expor coordenadas, segredo, stack trace, corpo bruto da fonte ou seed de credencial.
  - **Critério verificável:** `curl -fsS https://<API_HOST>/live` contém a declaração obrigatória e atribuição; `curl -fsS 'https://<API_HOST>/api/live/public?window=30d&series=<id>' | jq -e '.points | length <= 1000'` retorna `true`; acesso anônimo a `/api/live/runs/<id>` retorna 401 e com chave `live:read` retorna 200.
  - _Requisitos: 7.1–7.8, 8.4–8.6_

- [ ] **9. Validar custo, habilitar a agenda e executar a aceitação ponta a ponta**
  - Consultar preços atuais de `sa-east-1` pela AWS Price List API e documentar Fargate, IPv4, segredo, logs, armazenamento e transferência.
  - Confirmar estimativa incremental abaixo de US$ 10 antes de habilitar a agenda.
  - Executar uma tarefa manual; verificar origem, banco, H16, FFT, métricas, MQTT e painel.
  - Após aprovação explícita, habilitar o schedule e observar pelo menos três slots de cinco minutos sem duplicação.
  - **Critério verificável:** o relatório de custo soma menos de US$ 10/mês; `aws scheduler get-schedule --name nautam-live-production --region sa-east-1 --query State --output text` retorna `ENABLED`; `SELECT "slotUtc", status, source FROM "LiveRun" ORDER BY "slotUtc" DESC LIMIT 3;` retorna três slots distintos; `curl -fsS https://<API_HOST>/api/live/public?window=24h | jq -e '.latest.status == "succeeded" and .disclaimer != null'` retorna `true`.
  - _Requisitos: 2.1–2.6, 5.1–6.5, 7.1–7.8, 8.7–8.8_
