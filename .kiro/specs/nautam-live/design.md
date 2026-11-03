# Documento de Design — Nautam Live

## 1. Visão geral

O Nautam Live será uma extensão pequena da API existente. Uma tarefa ECS/Fargate efêmera, disparada pelo EventBridge Scheduler a cada cinco minutos, buscará medições públicas, persistirá sua proveniência no PostgreSQL, converterá até 12 valores em amplitudes dos canais HPM 1.0, produzirá um sinal composto com ruído controlado e executará a decodificação FFT existente. A mesma aplicação Fastify publicará uma página HTML com o resultado mais recente e a série histórica.

A arquitetura não adiciona serviço permanente, banco, load balancer, NAT Gateway ou broker MQTT. Ela reutiliza:

- `server/src/protocol/h16.ts`: `HPM10_F0`, `channelTable`, `compositeSignal` e `decodeFft`;
- `server/src/db.ts`: cliente Prisma e encerramento da conexão;
- `server/Dockerfile`: a imagem `runtime`, com sobrescrita do comando para o job;
- `server/prisma/schema.prisma`: banco PostgreSQL existente;
- `.github/workflows/deploy-aws.yml`: build, ECR, OIDC, migração e deploy;
- VPC, sub-redes, security groups, papéis e Secrets Manager existentes.

### Objetivo de desenho

Provar de forma reprodutível que o software Nautam consegue representar e recuperar canais H16 sob ruído sintético conhecido, usando valores observados no mundo real como carga útil. O produto não afirmará desempenho de enlace físico.

### Fora de escopo

Hardware, rádio, antena, propagação, BER física, consumo energético, OSINT, varredura de redes, IoT Core, broker MQTT, contas de usuário, billing, multiambiente e observabilidade avançada.

---

## 2. Pesquisa de fontes públicas

Pesquisa realizada em 03/11/2026. “Quantidade no Brasil” significa quantidade que a fonte documenta ou que pode ser obtida de forma verificável; não foi inferida a partir de pontos visuais em mapas. Quando uma informação não foi publicada pela fonte, a tabela registra **não confirmado**.

### 2.1 Matriz de fontes

| Fonte | Endpoint/acesso | Formato | Frequência publicada | Autenticação | Limite de taxa | Quantidade no Brasil | Licença e uso comercial | Decisão |
|---|---|---|---|---|---|---|---|---|
| **OpenAQ v3** | `GET https://api.openaq.org/v3/locations?iso=BR`; depois `GET /v3/locations/{id}/latest` ou `GET /v3/sensors/{id}/measurements`. A documentação mostra o filtro ISO e os recursos por localização/sensor ([Get locations](https://docs.openaq.org/api/operations/locations_get_v3_locations_get), [Latest](https://docs.openaq.org/resources/latest), [Measurements](https://docs.openaq.org/resources/measurements)). | REST/JSON ([About the API](https://docs.openaq.org/about/about)). | Varia por provedor e sensor; o endpoint `latest` entrega a medição mais recente e os endpoints horários podem agregar fontes mais frequentes ([Latest](https://docs.openaq.org/resources/latest), [hourly measurements](https://docs.openaq.org/api/operations/sensor_hourly_measurements_get_v3_sensors__sensors_id__hours_get)). | Chave em `X-API-Key` ([API key](https://docs.openaq.org/using-the-api/api-key)). | A OpenAQ aplica limite por chave e informa estado por headers; não publica na página consultada um número universal estático ([rate limits](https://docs.openaq.org/using-the-api/rate-limits)). O adaptador deve ler os headers e tratar `429`. | Dinâmica. Deve ser obtida do `meta.found` da consulta `iso=BR`; não foi confirmada nesta pesquisa porque o endpoint exige chave e o ambiente bloqueou a chamada. | A licença é informada por localização e pelo recurso `licenses`; há campos para uso comercial, modificação e redistribuição ([licenses](https://docs.openaq.org/resources/licenses), [locations](https://docs.openaq.org/resources/locations)). A OpenAQ avisa que dados são públicos, mas o usuário continua responsável pelos termos de terceiros ([about](https://docs.openaq.org/about/about)). | **Fonte inicial**, somente para localização fixa, proprietário institucional e licença comercial/redistribuição permitidas. |
| **Sensor.Community** | Endpoint comunitário observado na documentação/fórum: `GET https://data.sensor.community/airrohr/v1/filter/country=BR` e `GET .../sensor/{id}/` ([API por sensor](https://forum.sensor.community/t/is-there-a-public-url-for-my-sensor/1570), [wiki de APIs](https://github.com/opendata-stuttgart/meta/wiki/APIs)). | JSON no endpoint atual; arquivo histórico diário CSV ([wiki de APIs](https://github.com/opendata-stuttgart/meta/wiki/APIs)). | O firmware padrão envia aproximadamente a cada 145 segundos ([intervalo do firmware](https://forum.sensor.community/t/how-often-should-i-send-data-to-https-api-sensor-community-v1-push-sensor-data/785)). | O endpoint público de leitura é usado sem chave nos exemplos comunitários; não foi encontrada garantia formal de autenticação ou SLA. | Não confirmado; não foi encontrada cota oficial publicada. | Dinâmica; não foi possível contar porque o endpoint retornou 403 a partir deste ambiente. Não foi encontrada contagem oficial por país. | O projeto se descreve como rede de dados ambientais abertos ([site](https://sensor.community/en/)), mas não foi localizada licença inequívoca dos dados que confirme redistribuição comercial. A página de privacidade cobre dados pessoais, não substitui licença do banco ([privacy terms](https://sensor.community/en/privacy-terms/)). | **Não selecionar no MVP** até confirmação escrita de licença e revisão de geoprivacidade. Sensores domésticos podem tornar coordenadas e identificadores vinculáveis a pessoas. |
| **ONS Dados Abertos em S3** | Bucket `s3://ons-aws-prod-opendata`, ARN `arn:aws:s3:::ons-aws-prod-opendata`, em `sa-east-1` ([registro oficial no Open Data on AWS](https://github.com/awslabs/open-data-registry/blob/main/datasets/ons-opendata-portal.yaml)). Catálogo: [dados.ons.org.br](https://dados.ons.org.br/dataset/). | O catálogo oferece recursos CSV, JSON, Parquet e planilhas conforme o conjunto; por exemplo, a área de programação lista JSON, Parquet e CSV ([grupo de operação](https://dados.ons.org.br/group/programacao-da-operacao)). | O registro do bucket indica atualização diária; conjuntos específicos possuem granularidade horária ou semi-horária, como balanço horário e carga programada semi-horária ([registro AWS](https://github.com/awslabs/open-data-registry/blob/main/datasets/ons-opendata-portal.yaml), [balanço](https://dados.ons.org.br/dataset/balanco-energia-subsistema), [carga programada](https://dados.ons.org.br/dataset/carga-energia-programada)). | Leitura pública do bucket do programa Open Data on AWS; usar requisição S3 sem assinatura. | Não há cota de aplicação publicada pelo ONS; aplicam-se limites operacionais do S3. O adaptador deve fazer uma leitura incremental pequena. | Não se aplica como contagem de sensores. O ONS publica séries agregadas e séries por usina/reservatório, não um inventário nacional de sensores. | **CC BY 4.0** no registro oficial. A licença permite uso comercial com atribuição e indicação de mudanças ([registro AWS](https://github.com/awslabs/open-data-registry/blob/main/datasets/ons-opendata-portal.yaml), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.en)). | **Fonte de reserva**. É legalmente clara e está na mesma região, mas o painel deve mostrar sua cadência real; ela não substitui uma medição de cinco minutos. |
| **INMET** | Manual oficial: [API de estações](https://portal.inmet.gov.br/manual/manual-de-uso-da-api-esta%C3%A7%C3%B5es). Integrações existentes apontam historicamente para `https://apitempo.inmet.gov.br`, mas a estabilidade atual do endpoint não foi confirmada ([referência de integração](https://github.com/ThiagoRBM/API_INMET)). | Historicamente JSON para estações e séries; o formato atual deve ser validado no manual antes do uso. | Estações automáticas captam dados a cada hora; convencionais, três vezes ao dia ([INMET — sobre meteorologia](https://portal.inmet.gov.br/sobre-meteorologia)). | Não confirmado. Há relato de mudança de acesso, portanto não se deve assumir endpoint anônimo ([inmetpy](https://github.com/ocfgaldino/inmetpy)). | Não confirmado. | O INMET informa administrar mais de 700 estações no país ([sobre meteorologia](https://portal.inmet.gov.br/sobre-meteorologia)). Isso inclui tipos diferentes e não equivale a estações automáticas disponíveis pela API. | O INMET afirma que os dados são públicos, gratuitos e acessíveis em tempo real pelo portal ([acesso aos dados](https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-meteorol%C3%B3gicos-dispon%C3%ADveis-no-site-do-inmet)), mas não foi encontrada licença específica que autorize redistribuição comercial. | **Candidata futura**, após confirmação de API, cota e licença. |
| **Defesa Civil RS** | Página oficial da [API de Dados Hidrometeorológicos](https://sistemas.defesacivil.rs.gov.br/api-redehidrometeorologica), com consultas GraphQL `tags_data` e `historic`. | GraphQL/JSON. | A API entrega blocos de cinco minutos; a rede subjacente divulga atualização em segundos ([API](https://sistemas.defesacivil.rs.gov.br/api-redehidrometeorologica), [rede](https://defesacivil.rs.gov.br/estacoes-de-monitoramento-hidrologico)). | Não confirmado na documentação indexada. | Não confirmado. | A imprensa reportou 129 estações em operação, mas não foi localizada contagem equivalente na documentação da API; portanto a quantidade oficial utilizável permanece não confirmada ([referência jornalística](https://gauchazh.clicrbs.com.br/colunistas/rodrigo-lopes/noticia/2026/07/todas-as-estacoes-de-monitoramento-hidrometeorologico-da-defesa-civil-do-rs-estao-operando-segundo-o-governo-cmrzbp2uk01wn014c8pm6o2hw.html)). | Não foi localizada licença de redistribuição e uso comercial na página da API. Ser público e governamental, isoladamente, não substitui uma licença específica. | **Melhor candidata brasileira tecnicamente**, mas bloqueada para o MVP até confirmação jurídica. |
| **Rio de Janeiro — Alerta Rio/INEA/Dados.Rio** | Catálogo/API municipal: [api.dados.rio/docs](https://api.dados.rio/docs/); Alerta Rio: [estações](https://www.sistema-alerta-rio.com.br/info-estacoes/); INEA: [monitoramento hidrometeorológico](https://www.inea.rj.gov.br/ar-agua-e-solo/monitoramento-hidrometeorologico/). Não foi localizado endpoint oficial estável do conjunto de sensores. | A API municipal é HTTP/JSON; o Alerta Rio também publica páginas e tabelas. O formato específico da série não foi confirmado. | Alerta Rio usa registros de chuva de 15 minutos; o INEA informa registros a cada 15 minutos ([Alerta Rio](https://www.sistema-alerta-rio.com.br/24-horas/), [INEA](https://www.inea.rj.gov.br/ar-agua-e-solo/monitoramento-hidrometeorologico/)). | Não confirmado para o conjunto de sensores. | Não confirmado. | O INEA informa pouco mais de 100 estações automáticas no estado; não equivale à quantidade da API municipal nem apenas à cidade do Rio ([INEA](https://www.inea.rj.gov.br/ar-agua-e-solo/monitoramento-hidrometeorologico/)). | O portal municipal define dados abertos como reutilizáveis para qualquer finalidade, sujeito à proveniência e à licença ([Transparência Rio](https://transparencia.prefeitura.rio/dados-abertos/)); a licença do conjunto de sensores não foi confirmada. | **Não selecionar** sem endpoint e licença do conjunto. |
| **São Paulo — CETESB** | Mapa público com resumo da última hora: [mapa de qualidade do ar](https://sistemasinter.cetesb.sp.gov.br/Ar/php/mapa_qualidade_interior.php). A CETESB anunciou migração para ArcGIS, cuja API REST pode expor Feature Services, mas o endpoint exato do layer não foi localizado ([anúncio CETESB](https://cetesb.sp.gov.br/blog/2024/12/13/cetesb-migra-mapas-de-qualidade-do-ar-e-praias-para-a-plataforma-arcgis/), [ArcGIS Feature Service](https://developers.arcgis.com/documentation/mapping-apis-and-services/data-hosting/services/feature-service/)). | Página web e, potencialmente, ArcGIS REST/JSON. | Dados horários no mapa ([mapa CETESB](https://sistemasinter.cetesb.sp.gov.br/Ar/php/mapa_qualidade_interior.php)). | Não confirmado. | Não confirmado. | Foram divulgadas 62 estações automáticas e 22 manuais em 2025; uma notícia de 2026 menciona 85 estações no total ([SEMIL 2025](https://semil.sp.gov.br/2025/07/pulmoes-eletronicos-de-sao-paulo-como-a-cetesb-monitora-o-ar-que-voce-respira/), [SEMIL 2026](https://semil.sp.gov.br/2026/10/como-o-el-nino-pode-afetar-a-qualidade-do-ar-em-sao-paulo-cetesb-monitora-poluentes-em-85-estacoes/)). | O catálogo é descrito como dados abertos, mas não foi encontrada licença específica do layer em tempo real que confirme uso comercial ([catálogo CETESB](https://cetesb.sp.gov.br/blog/2024/09/09/cetesb-da-transparencia-a-dados-ambientais-do-estado-de-sao-paulo/)). | **Não selecionar** sem endpoint e licença do layer. |
| **Curitiba/Paraná — Dados Abertos e SIMEPAR** | Portal: [dadosabertos.curitiba.pr.gov.br](https://dadosabertos.curitiba.pr.gov.br/); visualização do SIMEPAR: [dados das estações](https://simepar.org/). Não foi localizada API pública documentada de sensores. | Arquivos do portal e página web do SIMEPAR; API/formato não confirmados. | A página apresenta valores correntes, mas a cadência não foi publicada na fonte consultada. | Não confirmado. | Não confirmado. | Não confirmado. | O portal municipal declara informações governamentais de domínio público para livre utilização ([Portal de Curitiba](https://dadosabertos.curitiba.pr.gov.br/)); não foi localizada licença dos dados do SIMEPAR nem autorização de redistribuição comercial. | **Não selecionar** sem API, cadência e licença. |
| **LoRaWAN público — TTN Mapper/The Things Network** | O TTN Mapper recebe medições de cobertura e mantém componentes de ingestão e feed ao vivo ([desenvolvimento](https://docs.ttnmapper.org/DEVELOPMENT.html), [ingress API](https://github.com/ttnmapper/ingress-api)). O Packet Broker oferece API para localização/status de gateways ([Packet Broker Mapper API](https://www.thethingsindustries.com/docs/concepts/packet-broker/api/)). | JSON/websocket para componentes específicos; não há endpoint público de leitura estável documentado para uma série brasileira de sensores ambientais. | Determinada pelos dispositivos contribuidores; sem cadência garantida. | Varia por componente/rede; dados de aplicação do TTN exigem credenciais da aplicação e não são um feed público geral. | Não confirmado para leitura pública. A Fair Access Policy da rede trata tempo no ar do dispositivo, não uma cota de API. | Não confirmada. Mapas só contam gateways com localização pública, portanto não representam toda a cobertura ([comunidade Brasília](https://thethingsnetwork.org/community/brasilia/)). | O TTN Mapper declara PDDL 1.0 para seus dados, permitindo uso sem restrições ([FAQ](https://docs.ttnmapper.org/FAQ.html), [PDDL](https://opendatacommons.org/licenses/pddl/1-0/)). Isso não concede acesso a payloads privados de aplicações LoRaWAN. | **Fora do MVP**: é fonte de cobertura, não feed público geral de sensores. |

### 2.2 Escolha e fail-closed legal

**Escolha inicial: OpenAQ v3.** Ela possui contrato REST documentado, medições por sensor, autenticação por chave e metadados de licença por localização. O adaptador não confiará no rótulo genérico “open”: exigirá os campos que autorizem uso comercial e redistribuição, registrará a atribuição e recusará proprietário individual ou estação móvel.

**Reserva: ONS no S3 público.** O bucket está em `sa-east-1` e tem CC BY 4.0 explícita. A reserva mantém a demonstração com uma série brasileira e legalmente reutilizável, mas o painel mostrará “fonte de reserva”, a granularidade original e a idade do registro. Não haverá interpolação nem atualização artificial do timestamp.

**Sensor.Community não será reserva no MVP.** Apesar da boa frequência, a pesquisa não encontrou licença inequívoca dos dados e a localização de um sensor comunitário pode ser associada a uma residência. Ativar essa fonte antes de resolver licença e geoprivacidade criaria risco desnecessário.

---

## 3. LGPD, atribuição e minimização

A LGPD define dado pessoal como informação relacionada a pessoa natural identificada ou identificável ([Lei 13.709/2018, art. 5º, síntese oficial](https://www.gov.br/defesa/pt-br/acesso-a-informacao/lei-geral-de-protecao-de-dados-pessoais-lgpd)). O fato de um dado estar disponível publicamente não elimina automaticamente sua natureza pessoal. Localização precisa e padrões temporais podem permitir reidentificação; a literatura de geoprivacidade documenta esse risco em dados de sensoriamento participativo ([survey sobre geodados](https://arxiv.org/pdf/2402.03612.pdf), [guideline de participatory sensing](https://pmc.ncbi.nlm.nih.gov/articles/PMC6011384/)).

O conjunto escolhido para o MVP conterá apenas:

- valor físico, unidade e parâmetro;
- instante da observação;
- identificadores técnicos do provedor, localização e sensor;
- nome institucional da estação/provedor;
- licença, atribuição e URL de origem;
- município/UF quando necessário à exibição.

Não serão ingeridos nomes de contribuidores, e-mails, contatos, endereços, identificadores de contas, trajetórias, imagens ou coordenadas exatas de estações comunitárias/móveis. Embora a OpenAQ informe que proprietários podem ser indivíduos ([Owners](https://docs.openaq.org/resources/owners)), o filtro do MVP aceitará apenas proprietários institucionais e localizações fixas. O endpoint público não retornará latitude/longitude; isso reduz utilidade de reidentificação sem prejudicar a prova do protocolo.

A conclusão jurídica é limitada: **o recorte proposto não contém campos destinados a identificar pessoa natural**. Isso não equivale a parecer jurídico nem garante que um provedor nunca publique metadado pessoal. A qualificação fail-closed e a lista explícita de campos são os controles do MVP.

---

## 4. Arquitetura proposta

```text
EventBridge Scheduler — rate(5 minutes)
             |
             | ecs:RunTask
             v
ECS/Fargate task (mesma imagem API, comando live:run)
  1. reivindica slot UTC único no RDS
  2. consulta OpenAQ; se necessário, ONS S3
  3. qualifica licença/proprietário e normaliza até 12 observações
  4. channelTable -> compositeSignal -> AWGN -> decodeFft
  5. calcula métricas + baseline MQTT
  6. grava resultado e encerra
       | HTTPS público                    | DATABASE_URL
       v                                  v
OpenAQ / ONS S3                    RDS PostgreSQL privado
                                           ^
                                           |
Internet -> ALB/HTTPS -> Fastify existente |
                          /live             |
                          /api/live/public -+
```

### 4.1 Decisão de hospedagem do painel

O painel será uma página leve servida pelo Fastify existente, com HTML/CSS/JavaScript sem framework adicional obrigatório. Ele consultará um resumo público com limites rígidos. Essa decisão evita uma segunda tarefa Fargate permanente, um segundo IP público e outro deploy de frontend.

A abertura de `/live` e `/api/live/public` é uma exceção intencional e estreita à regra anterior de proteger rotas de dados. O endpoint público contém somente observações já públicas, qualificadas e sem coordenadas, além de métricas da simulação. Dados brutos, administração e reprocessamento continuam sob chave com escopo `live:read` ou `live:write`.

### 4.2 Agendamento

O EventBridge Scheduler suporta expressões recorrentes, janela flexível, política de retry e idade máxima da entrega ([guia do Scheduler](https://docs.aws.amazon.com/eventbridge/latest/userguide/using-eventbridge-scheduler.html)). A configuração proposta é:

```text
name: nautam-live-production
schedule: rate(5 minutes)
flexible time window: OFF
state: ENABLED
maximum event age: 240 segundos
maximum retry attempts: 2
target: ECS RunTask / FARGATE
command override: ["node", "dist/cli/nautam-live.js"]
```

Não se propõe DLQ no primeiro corte. O Scheduler só confirma que `RunTask` foi aceito; falhas posteriores do contêiner serão representadas pelo estado persistido e por logs. Uma DLQ SQS poderá ser adicionada se falhas de entrega forem observadas; o Scheduler suporta DLQ após esgotar retries ([DLQ do Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/configuring-schedule-dlq.html)).

### 4.3 Rede e IAM

- a tarefa usa as sub-redes públicas já usadas pela migração, com IP público apenas durante sua execução para alcançar as fontes HTTPS;
- o RDS continua privado;
- o security group do job não possui ingress e permite egress HTTPS e PostgreSQL conforme a topologia existente;
- o papel do Scheduler permite somente `ecs:RunTask` para a família do job e `iam:PassRole` para os papéis de execução/tarefa;
- o papel de execução lê `DATABASE_URL` e a chave OpenAQ específica;
- o papel da aplicação não precisa criar segredos nem modificar infraestrutura;
- o workflow OIDC registra a task definition e atualiza o schedule, mas não recebe o valor dos segredos.

---

## 5. Componentes de software

### 5.1 `LiveSourceAdapter`

Contrato interno proposto:

```ts
interface SourceObservation {
  provider: 'openaq' | 'ons'
  stationRef: string
  sensorRef: string
  parameter: string
  value: number
  unit: string
  observedAt: Date
  sourceUrl: string
  licenseName: string
  licenseUrl: string
  attribution: string
  institutionalOwner: boolean
  mobile: boolean
  commercialUseAllowed: boolean
  redistributionAllowed: boolean
}

interface LiveSourceAdapter {
  fetchLatest(signal: AbortSignal): Promise<SourceObservation[]>
}
```

O adaptador OpenAQ seleciona no máximo 12 combinações estáveis de sensor/parâmetro. O adaptador ONS seleciona uma série pequena e conhecida, por exemplo balanço horário por subsistema, e converte cada série num `SourceObservation` sem alterar o timestamp original.

### 5.2 Seleção e atribuição de canais

1. descartar valores não finitos, unidade ausente, licença inelegível e timestamps futuros;
2. descartar registros mais antigos que o limite da fonte, mas registrar `no_new_data` em vez de fabricar leitura;
3. ordenar pela chave `provider/stationRef/sensorRef/parameter`;
4. selecionar no máximo 12 chaves estáveis;
5. atribuir canal por índice nessa ordem, preservando a chave no registro;
6. quando um sensor faltar, não deslocar os demais canais dentro da execução: a configuração persistida registra o mapa efetivo.

Para continuidade visual, uma tabela de configuração poderá fixar as 12 chaves selecionadas após a qualificação inicial. O MVP não precisa de um sistema genérico de cadastro de fontes.

### 5.3 Normalização de amplitude

Cada parâmetro terá uma faixa declarada em código, com unidade canônica. O valor original nunca é substituído. A amplitude é:

```text
x = clamp((valor - mínimo) / (máximo - mínimo), 0, 1)
amplitude = 0,10 + 0,90 × x
```

O piso 0,10 evita representar um valor válido como ausência de canal. O registro contém `clipped=true` quando houver saturação. Conversões de unidade devem ser explícitas e testáveis.

### 5.4 Síntese e ruído

Parâmetros iniciais compatíveis com a rota FFT existente:

```text
f0 = 16.384 Hz
sampleRate = 131.072 amostras/s
duration = 1/64 s
N = 2.048 amostras
thresholdDb = -40 dB
SNR operacional = 20 dB
```

A resolução em frequência é `Δf = sampleRate / N = 1 / duration = 64 Hz`; FFTs discretas organizam os bins em múltiplos de `1/(N·d)` ([SciPy fftfreq](https://docs.scipy.org/doc/scipy/reference/generated/scipy.fftpack.fftfreq.html)). Esses números são parâmetros de simulação, não largura de banda homologada.

O ruído AWGN será calculado com semente persistida:

```text
P_s = média(s[i]²)
SNR_linear = 10^(snrDb/10)
σ = sqrt(P_s / SNR_linear)
y[i] = s[i] + Normal(0, σ²)
SNR_medido = 10·log10(P_s / média((y[i]-s[i])²))
```

A semente deve gerar a mesma sequência na mesma versão do algoritmo. O painel mostra SNR solicitado e medido.

### 5.5 Recuperação de amplitude

A magnitude FFT não será assumida como amplitude física. Para cada canal, uma referência limpa de amplitude unitária será processada pelo mesmo `compositeSignal`/`decodeFft`, produzindo ganho `g_k`. A estimativa será `Â_k = magnitude_k / g_k`. Isso neutraliza fatores internos de normalização sem duplicar o decoder. O erro exibido é calculado contra a amplitude normalizada esperada, não contra a grandeza física original.

---

## 6. Métricas experimentais

### 6.1 Detecção de canais

Um pico corresponde a um canal esperado quando:

- a razão H16 decodificada é a razão esperada; e
- o erro de frequência é no máximo `Δf/2`.

Definições por execução:

```text
TP = canais esperados encontrados uma vez
FN = canais esperados não encontrados
FP = picos aceitos que não correspondem a canal esperado
recall/taxa de acerto = TP / (TP + FN)
precisão = TP / (TP + FP)
MAE_amplitude = média(|Â_k - A_k|) nos TP
tempo_ms = fim_monotônico - início_monotônico
```

Com payload por presença/amplitude, “taxa de acerto” é mais adequada que BER: o MVP não define símbolos binários, codificação de canal ou demodulador de bits. Literatura de sistemas multicarrier costuma avaliar erro em função de SNR e interferência entre portadoras; deslocamento de frequência degrada ortogonalidade e cria interferência interportadora ([análise OFDM/CFO](https://eprints.soton.ac.uk/263941/1/28.pdf)). O Nautam Live não será chamado de OFDM e não herdará suas garantias; a referência apenas sustenta as dimensões de medição.

### 6.2 SNR mínima testada

Uma vez por dia, a execução fará um sweep pequeno:

```text
SNRs: [30, 20, 15, 10, 5, 0, -5] dB
repetições: 20 sementes por SNR
critério: recall >= 95% e precisão >= 99%
resultado: menor SNR testada que atende ao critério, ou “não atingida”
```

O painel deve dizer “menor SNR testada”, nunca “limite teórico”. Vinte repetições produzem evidência exploratória, não intervalo estatístico estreito; a contagem deve ser exibida.

### 6.3 Razões/canais vizinhos

Os pares HPM serão ordenados pela separação absoluta de frequência. Os três pares mais próximos serão testados isoladamente e com todos os canais ativos. Para cada par:

```text
separação_hz = |f_i - f_j|
separação_bins = separação_hz / Δf
recall_do_par = detecções_corretas / (2 × repetições)
```

O teste é necessário porque uma janela finita pode espalhar energia entre bins; o NIST documenta que janelas e hipótese sobre dados fora da captura afetam estimativas espectrais ([FFT para experimentalistas](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=150010), [artefatos FFT](https://www.nist.gov/publications/eliminating-fft-artifacts-vector-signal-analyzer-spectra)).

### 6.4 Capacidade declarada

O MVP reportará:

- até 12 valores por quadro;
- duração configurada do quadro;
- `valores_por_segundo_simulado = valores / duração`;
- N amostras e tamanho `N × 8` bytes quando materializado em `Float64`;
- tempo real de CPU para sintetizar e decodificar.

Não será aplicada a fórmula de Shannon para declarar capacidade do Nautam, pois ela exige largura de banda e modelo físico de canal. A fórmula Shannon-Hartley é um limite para canal AWGN de banda limitada, não uma medição desta simulação ([IEEE Technology Navigator](https://technav.ieee.org/topic/channel-capacity)).

---

## 7. Linha de base MQTT

A comparação usa MQTT 3.1.1 e uma única publicação em lote no tópico UTF-8 `nautam/live/readings`. A carga útil canônica será o mesmo conjunto lógico de leituras, com chaves e ordenação determinísticas. A especificação MQTT define o pacote de controle com cabeçalho fixo, Remaining Length, tópico no cabeçalho variável e Packet Identifier para QoS maior que zero ([MQTT 3.1.1 OASIS](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)).

Para payload de `P` bytes e tópico de `T` bytes:

```text
variable_header_qos0 = 2 + T
variable_header_qos1 = 2 + T + 2
remaining = variable_header + P
remaining_length_bytes = tamanho do inteiro MQTT em base 128
publish_total = 1 + remaining_length_bytes + remaining
mqtt_overhead = publish_total - P
qos1_exchange_total = publish_total + 4  # PUBACK sem propriedades em MQTT 3.1.1
```

O painel separa:

- bytes do JSON canônico;
- overhead PUBLISH QoS 0;
- overhead PUBLISH e PUBACK QoS 1;
- bytes do vetor de amostras `Float64` apenas como representação computacional.

CONNECT/CONNACK são amortizados assumindo conexão persistente. TCP, IPv4/IPv6, TLS, Ethernet, rádio, keepalive, retransmissões, sessão do broker e energia ficam fora. A comparação não afirma que amostras `Float64` seriam enviadas literalmente por um enlace Nautam nem que MQTT é uma camada física.

---

## 8. Modelo de dados

Migração Prisma proposta, inteiramente aditiva:

```prisma
model LiveRun {
  id               Int       @id @default(autoincrement())
  slotUtc          DateTime  @unique
  source           String
  status           String
  sourceObservedAt DateTime?
  f0               Float     @default(16384)
  sampleRate       Int       @default(131072)
  durationSeconds  Float     @default(0.015625)
  thresholdDb      Float     @default(-40)
  requestedSnrDb   Float?
  measuredSnrDb    Float?
  noiseSeed        String?
  expectedChannels Json?
  decodedPeaks     Json?
  metrics          Json?
  mqttBaseline     Json?
  errorCode        String?
  startedAt        DateTime  @default(now())
  completedAt      DateTime?
  observations     LiveObservation[]

  @@index([completedAt])
  @@index([status, slotUtc])
}

model LiveObservation {
  id                  Int      @id @default(autoincrement())
  runId               Int
  provider            String
  stationRef          String
  sensorRef           String
  parameter           String
  originalValue       Float
  unit                String
  observedAt          DateTime
  ingestedAt          DateTime @default(now())
  normalizedAmplitude Float
  clipped             Boolean  @default(false)
  channelId           Int
  ratioA              Int
  ratioB              Int
  licenseName         String
  licenseUrl          String
  attribution         String
  sourceUrl           String
  run                  LiveRun  @relation(fields: [runId], references: [id])

  @@unique([provider, sensorRef, parameter, observedAt])
  @@index([runId, channelId])
  @@index([parameter, observedAt])
  @@index([observedAt])
}
```

`slotUtc` é o início do intervalo UTC de cinco minutos. A tarefa tenta criar `LiveRun` com esse valor dentro de transação. Conflito único significa que outra execução já reivindicou o slot; a tarefa encerra sem duplicar processamento.

Estados permitidos por código: `running`, `succeeded`, `failed`, `no_new_data`. Não é necessário criar enum Prisma no primeiro corte; validação ocorre no domínio e evita migrações de enum mais rígidas.

---

## 9. API e painel

### 9.1 Rotas

| Método e rota | Acesso | Finalidade |
|---|---|---|
| `GET /live` | público | HTML do painel |
| `GET /api/live/public?window=24h&series=<id>` | público, limitado | última execução, histórico agregado e atribuição |
| `GET /api/live/runs/:id` | `live:read` | diagnóstico completo, inclusive configuração reproduzível |
| `POST /api/live/runs/:id/replay` | `live:write` | fora do fluxo normal; reprocessamento manual controlado |

O endpoint público aceita `window ∈ {24h,7d,30d}`, uma série por requisição e no máximo 1.000 pontos. Janelas longas são agregadas no servidor. Não retorna coordenadas, corpos externos, stack traces, segredo, seed de credencial ou detalhes IAM.

### 9.2 Estados da interface

- **normal**: última execução bem-sucedida há até 15 minutos;
- **desatualizado**: última execução bem-sucedida há mais de 15 minutos;
- **sem dados**: nenhuma execução bem-sucedida;
- **fonte de reserva**: ONS ativo, com cadência original destacada;
- **falha recente**: última tentativa falhou, mas o histórico anterior continua visível.

A frase obrigatória aparece junto às métricas:

> simulação de sinal com dados reais; energia e interferência em campo não medidas

A atribuição deve trazer fonte, provedor, licença, link da licença, URL de origem, instante observado e indicação de transformações: seleção, normalização, composição, ruído e FFT.

---

## 10. Tratamento de erros

| Falha | Comportamento |
|---|---|
| timeout, DNS ou `5xx` na OpenAQ | retry limitado; depois tenta ONS |
| `429` OpenAQ | respeita `Retry-After` se couber no limite de quatro minutos; senão tenta ONS |
| licença ausente/negativa | rejeita registro; nunca faz fallback “permissivo” |
| owner individual ou estação móvel | rejeita registro |
| nenhum dado novo | estado `no_new_data`; não repete timestamp como atual |
| violação de unicidade da observação | trata como duplicata, não como nova leitura |
| falha de FFT ou persistência | transação marca `failed`, logs estruturados sem payload externo completo |
| execução sobreposta | conflito em `slotUtc`; segunda tarefa encerra como no-op |
| painel/RDS indisponível | Fastify retorna erro controlado; `/api/readyz` continua refletindo banco |

---

## 11. Custo incremental

A agenda de cinco minutos produz `12 × 24 × 30,42 ≈ 8.760` invocações por mês. O EventBridge Scheduler inclui 14 milhões de invocações mensais gratuitas; 8.760 ficam muito abaixo dessa franquia ([preços EventBridge](https://aws.amazon.com/eventbridge/pricing/)).

Fargate cobra vCPU, memória e armazenamento desde o início do pull da imagem até a parada, por segundo, com mínimo de um minuto por tarefa ([preços Fargate](https://aws.amazon.com/fargate/pricing/)). Para orçamento, deve-se assumir um minuto cobrado por disparo mesmo que o job termine antes:

```text
8.760 minutos = 146 horas-tarefa/mês
configuração: 0,25 vCPU e 0,5 GB
```

| Item | Premissa mensal | Teto de orçamento |
|---|---:|---:|
| EventBridge Scheduler | 8.760 invocações, dentro da franquia | US$ 0,00 |
| Fargate Linux/x86 | 146 horas-tarefa de 0,25 vCPU/0,5 GB | US$ 3,00 |
| IPv4 público temporário | 146 horas × US$ 0,005/h | US$ 0,73 |
| Secrets Manager | uma chave OpenAQ adicional | US$ 0,50 |
| CloudWatch Logs | logs compactos, retenção de 14 dias | US$ 0,75 |
| RDS gp3 incremental | até ~350 mil observações/90 dias, dentro do volume atual | US$ 0,50 |
| transferência externa | respostas pequenas, sem arquivos grandes | US$ 0,50 |
| **Total orçado** |  | **US$ 5,98/mês** |

A AWS cobra US$ 0,005 por hora de IPv4 público além das franquias aplicáveis ([anúncio AWS](https://aws.amazon.com/id/about-aws/whats-new/2024/02/aws-free-tier-750-hours-free-public-ipv4-addresses/)). Os preços exatos de Fargate, logs, segredo e armazenamento variam por região/uso; antes da implementação, o valor de `sa-east-1` deve ser consultado pela AWS Price List API, que permite filtrar produtos e região ([Price List Query API](https://docs.aws.amazon.com/pt_br/awsaccountbilling/latest/aboutv2/using-price-list-query-api.html)). O teto tem margem de aproximadamente US$ 4,00 sobre a meta de US$ 10.

Não usar uma segunda tarefa permanente para o painel economiza Fargate e IPv4 durante 730 horas mensais. Não usar NAT Gateway evita seu custo fixo e processamento de dados.

---

## 12. Implantação e reversão

1. a migração aditiva passa pelo fluxo Prisma existente;
2. a imagem da API é criada e publicada uma vez;
3. o workflow registra a revisão da task definition do Nautam Live usando a mesma imagem e comando sobrescrito;
4. o schedule é criado/atualizado apontando para a revisão aprovada;
5. uma execução manual valida licença, ingestão, FFT e banco;
6. somente após validação o schedule é habilitado;
7. o deploy da API publica `/live` e `/api/live/public`;
8. reversão operacional: desabilitar o schedule e voltar a imagem da API; tabelas aditivas podem permanecer sem uso.

Nenhuma exclusão de dados ou downgrade de migração é necessário para reverter o recurso.

---

## 13. Decisões adiadas

- Sensor.Community após licença e geoprivacidade;
- Defesa Civil RS após confirmação escrita de licença, autenticação e cota;
- DLQ SQS após evidência de falha de entrega do Scheduler;
- CloudWatch Alarm, tracing e métricas customizadas;
- frontend Next.js/Amplify ou dashboard Streamlit dedicado;
- retenção/particionamento de tabelas após medir crescimento;
- comparação experimental com broker MQTT real;
- hardware e ensaios RF.

---

## 14. Incertezas e itens não confirmados

1. **OpenAQ no Brasil:** não foi possível confirmar a quantidade atual de localizações/sensores, provedores brasileiros específicos nem a licença de uma localização concreta sem uma chave. A E1 deve consultar `meta.found` e qualificar as licenças antes de qualquer ingestão.
2. **Limite OpenAQ:** a documentação confirma limites por chave e headers, mas não apresentou um número universal estático na pesquisa. O adaptador deve obedecer ao limite recebido em runtime.
3. **Sensor.Community:** quantidade no Brasil, rate limit e licença inequívoca para redistribuição comercial não foram confirmados. O endpoint respondeu 403 a partir deste ambiente.
4. **Defesa Civil RS:** a página documenta GraphQL e blocos de cinco minutos, porém autenticação, rate limit e licença comercial não foram confirmados.
5. **INMET:** o portal afirma dados públicos e gratuitos, mas a autenticação atual da API, rate limit e licença de redistribuição comercial não foram confirmados.
6. **Rio, São Paulo e Curitiba:** não foi possível confirmar, ao mesmo tempo, endpoint oficial estável, rate limit e licença comercial do conjunto em tempo real.
7. **LoRaWAN:** o TTN Mapper licencia seus próprios dados por PDDL, mas não oferece, na documentação encontrada, um feed público estável de payloads ambientais do Brasil; payloads de aplicações TTN não são públicos por padrão.
8. **Custos:** preços exatos de Fargate e CloudWatch em `sa-east-1` não foram consultados em uma conta AWS. O orçamento é um teto de design que deve ser validado pela Price List API antes da E1.
9. **Tempo do job:** não foi medido quanto a imagem existente demora para iniciar e executar o sweep diário no Fargate. O limite de quatro minutos deve ser validado; se necessário, o sweep passa para execução diária separada sem serviço permanente.
10. **Amplitude FFT:** a normalização interna de magnitude deve ser confirmada por teste contra referência unitária; por isso o design usa calibração empírica em vez de assumir um fator teórico.
11. **LGPD:** a minimização proposta evita campos destinados a identificar pessoas, mas não substitui aconselhamento jurídico e não garante que metadados futuros do provedor jamais incluam informação pessoal.

---

## 15. Fontes e conformidade de uso

As fontes externas estão ligadas no ponto em que sustentam cada afirmação. Conteúdo externo foi resumido e parafraseado; nenhum trecho extenso foi reproduzido. **Conteúdo foi reformulado para conformidade com restrições de licenciamento.**