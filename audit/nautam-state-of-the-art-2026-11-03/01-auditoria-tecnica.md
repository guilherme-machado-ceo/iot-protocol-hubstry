# Auditoria técnica — arquitetura, matemática, experimentos e operação

## 1. Método e escala de evidência

- **Confirmado:** observado em código, teste executado, log ou fonte externa primária.
- **Parcial:** há implementação, mas uma condição, integração ou prova relevante falta.
- **Não verificado:** não foi possível consultar o ambiente, artefato ou fonte necessária.

Documentação foi usada para localizar alegações, não para prová-las. O baseline é exclusivamente [`main@71fb8ea`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/tree/71fb8ea03241f48d1a63e3cc356ae07c8e094948). O [PR #54](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/54) aparece em seção separada.

## 2. Arquitetura efetiva

```text
Python standalone / Streamlit
  hale_core ──┐
  hpg_core  ──┼──> dashboard.py (demonstração local)
  security  ──┘
       |
       └── fixtures Python -> comparação no API CI -> h16.ts

Produção TypeScript
  fontes OpenAQ/ONS -> live/ingestao.ts -> live/protocolo.ts
                                            |  h16.ts
                                            v
                       PostgreSQL <- Prisma <- Fastify
                                                   |
                                      /api/* + /live
                                                   |
                                       ECS Express / ALB

Operação
  GitHub OIDC -> ECR -> migração ECS -> API ECS
  EventBridge Scheduler (script separado) -> task ECS Live
```

### 2.1 Mapa por componente

| Componente | Estado substantivo | Evidência |
|---|---|---|
| `hale_core` | Experimental, não integrado à API/Live | [`HALEPipeline`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hale_core/hale_equation.py#L96-L191) produz grade, hash e período; não é importado pelo runtime TypeScript. |
| `hpg_core` Python | Funcional como referência/gerador de fixture | [`signal_processing.py`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hpg_core/signal_processing.py#L18-L139); gera o oráculo usado pelos testes TS. |
| `server/src/protocol/h16.ts` | Núcleo realmente usado em produção | [`computeHn`, `compositeSignal`, FFT/DFT e decoder](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/protocol/h16.ts#L40-L182). |
| `server/src/live` | Pipeline E1/E2 implementado | [`ingestao.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/live/ingestao.ts#L1-L98), [`protocolo.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/live/protocolo.ts#L1-L213). |
| Fastify/Prisma/Live E3 | Integrado e testado localmente | [`index.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/index.ts#L28-L73), [`routes/live.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/routes/live.ts#L73-L164). |
| `security/` Python | Demonstração isolada do dashboard | HSL, LFSR e detecção por fase não são chamados pela API. |
| C++ `src/` | Protótipo separado | O CI tenta compilar o demo; `SecureConfig` é opcional e não integra Fastify/Live. |
| `demo-web/harmonic-demo` | Simulação visual separada e divergente | Usa valores aleatórios e f0 de 1 kHz; não consome a API Live. |
| Infra AWS | API implantada; operação Live parcial | [Deploy 41658882442](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658882442) passou. Agenda é criada/habilitada por script fora do workflow. |

## 3. Fundamentos matemáticos

### 3.1 Cardinalidade H16

O código enumera pares coprimos com numerador e denominador limitados por `N`. Por simetria em torno de `a=b` e porque o único par coprimo diagonal é `1/1`:

\[
|H_N|=2\sum_{k=1}^{N}\varphi(k)-1.
\]

Para N=16:

```text
Σφ(1..16) = 80
2Σφ - 1   = 159
```

**Confirmado independentemente** por script de enumeração durante a auditoria. O TypeScript declara e testa 159. O Python e o README declaram 80:

- enumeração quadrada: [`compute_hn`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hpg_core/omnigrid.py#L21-L37);
- fórmula unilateral errada para essa enumeração: [`cardinality_hn`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hpg_core/omnigrid.py#L40-L51);
- repetição da inconsistência no HALE: [`compute_cardinality`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hale_core/hale_equation.py#L108-L126);
- TypeScript correto: [`computeHn`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/protocol/h16.ts#L55-L66).

Consequências:

- `HALEPipelineResult.cardinality=80` pode coexistir com `grid_size=159`;
- a Omnigrid completa tem `318` elementos, não `160`;
- alegações de capacidade/endereço que usam 80 ou 160 não descrevem o conjunto implementado.

### 3.2 Frequências e Nyquist

HPM usa razões:

```text
1/1, 2/1, 3/2, 4/3, 5/4, 3/1,
5/3, 7/4, 7/5, 8/5, 5/2, 7/3
```

Com `f0=16.384 Hz`, a faixa HPM é 16.384–49.152 Hz. A taxa Live de 131.072 amostras/s dá Nyquist de 65.536 Hz e cobre HPM.

O H16 completo vai de `f0/16=1.024 Hz` a `16f0=262.144 Hz`; exigiria `Fs > 524.288 Hz`. A rota TS trata Nyquist explicitamente e rejeita componentes iguais ou acima dele. O núcleo Python usa por padrão `Fs=44.100 Hz` e os seis primeiros canais HPM; 2/1, 3/2 e 3/1 ficam acima de 22.050 Hz e sofrem aliasing silencioso. Evidência: [defaults Python](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/hpg_core/signal_processing.py#L18-L59) e [guarda TypeScript](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/routes/harmonic.ts#L120-L137).

### 3.3 Ortogonalidade

Para exponenciais complexas numa janela retangular T, tons distintos são ortogonais quando `(fk-fl)T` é inteiro. Para `fk=(ak/bk)f0`, uma condição suficiente é:

\[
T=m\operatorname{lcm}(b_1,\ldots,b_K)/f_0.
\]

Para HPM, `lcm=60`; a janela mínima é 3,662109375 ms e tem 480 amostras em 131.072 Hz. Para H16 inteiro, `lcm(1..16)=720720`, gerando 43,9892578125 s e 5.765.760 amostras nessa taxa, acima dos limites atuais.

O quadro Live usa `T=1/64 s`, `N=2048`, `Δf=64 Hz`. Os canais com denominador 3 ou 5 não completam ciclos inteiros:

| Canal | Razão | Ciclos no quadro | Distância do bin inteiro |
|---:|---:|---:|---:|
| 4 | 4/3 | 341,3333 | +0,3333 bin |
| 7 | 5/3 | 426,6667 | −0,3333 bin |
| 9 | 7/5 | 358,4 | +0,4 bin |
| 10 | 8/5 | 409,6 | −0,4 bin |
| 12 | 7/3 | 597,3333 | +0,3333 bin |

Cálculo amostral independente:

- quadro atual: correlação cruzada normalizada máxima `0,0065092544`, par CH7–CH8;
- janela coerente de 480 amostras: `5,30×10⁻¹⁵`, erro numérico.

A baixa correlação atual ajuda a aplicação porque os canais HPM são separados. Ela não sustenta “zero interference” nem “orthogonality mathematically guaranteed” para qualquer configuração.

### 3.4 Resolução e separação

A menor separação do H16 completo é entre `1/16` e `1/15`:

\[
\Delta f_{min}=f_0/240=68{,}2667\,Hz,
\]

apenas 1,0667 bins na resolução de 64 Hz. H16 completo não tem margem suficiente no quadro atual. O menor espaçamento HPM é `f0/15≈1092,27 Hz`, cerca de 17,07 bins, substancialmente mais favorável.

### 3.5 Janela, fase e amplitude

O Python e o TS aplicam FFT/DFT sem janela explícita, equivalente a janela retangular. Não há:

- correção de ganho coerente;
- integração multibin;
- interpolação de frequência;
- estimação de fase;
- ajuste conjunto dos tons.

O detector cego mantém magnitudes, normaliza pelo maior pico e localiza máximos locais estritos. Logo, `amplitude_db` é relativa ao próprio quadro, não nível físico. O receptor HPM conhecido lê um bin por canal e divide por ganho calibrado com tom unitário. Isso é eficaz no cenário fixo, mas não corrige integralmente leakage cruzado, phase offset, clock offset ou canal seletivo. A literatura clássica mostra o papel da janela em sinais harmônicos finitos: Harris, 1978, [DOI 10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837).

### 3.6 Complexidade

- síntese: `O(KN)`;
- FFT radix-2 TS: `O(N log N)`;
- fallback DFT TS: `O(N²)`;
- detecção de picos: `O(N)` mais busca racional;
- `computeHn`: `O(N²)` mais ordenação;
- período coerente do H16 cresce pelo MMC dos denominadores, não de forma prática.

A rota limita `N≤65536` para potência de dois e `N≤4096` para DFT. Não há evidência de 1.000 canais; a rota aceita no máximo 12 canais HPM ou 32 razões explícitas.

## 4. Validação experimental

### 4.1 Testes executados nesta auditoria

Em arquivo temporário criado por `git archive origin/main`:

```text
npm ci                   PASS
npm run typecheck        PASS
npm test                 PASS: 9 arquivos, 72 testes
npm run build            PASS
```

O diretório temporário foi removido ao final. Os resultados batem com o [API CI do commit](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658832142).

### 4.2 O que a paridade Python/TS prova

[`h16.test.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/tests/unit/h16.test.ts) compara nove fixtures geradas pelo próprio Python. Isso prova que as implementações produzem resultados próximos nos vetores cobertos. Não prova correção independente: um erro compartilhado pelo gerador e porte passa no teste.

A paridade cobre H16, tabela, amostras do sinal e picos. Não cobre HALE, funções ψ, Omnigrid/polaridade ou verificação espectral.

### 4.3 Ruído e estatística

[`varredura`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/live/protocolo.ts#L105-L133) executa 20 quadros em sete SNRs com presença aleatória de 75%. Pontos positivos:

- semente fixa e reprodução determinística;
- métricas separadas para receptor conhecido e detector cego;
- recall, precisão, MAE e falsos por quadro.

Limites:

- uma campanha/seed por run;
- ausência de intervalos de confiança e distribuição entre seeds;
- 20 quadros não sustentam com precisão alta um limiar de 95%; mesmo 0 falhas em 40 oportunidades deixa limite inferior binomial de 95% abaixo de 95%;
- o teste automatizado só exige que o receptor obtenha alguma SNR aprovada e que o cego não obtenha, sem fixar regressão em 15 dB;
- o ensaio de vizinhos calcula recall, mas o teste não exige um valor mínimo.

O texto “varredura diária” no `main` diverge da implementação: ela é recalculada em todo run que tem observações.

### 4.4 O que não existe

Não foram encontrados:

- vetores IQ de RF, captura ADC/DAC ou sinal de osciloscópio;
- transmissor/receptor em hardware ou SDR;
- BER/PER com framing e símbolos definidos;
- ensaios de energia;
- CFO, SFO, Doppler, fading, multipercurso ou interferência externa;
- PAPR, EVM, IIP2/IIP3, compressão ou máscara espectral;
- comparação justa com outro PHY no mesmo hardware/canal/potência.

## 5. Nautam Live ponta a ponta

### 5.1 Fonte e qualificação OpenAQ

O script [`qualificar-openaq.sh`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/deploy/live/qualificar-openaq.sh) exige estação fixa, monitor de referência, leitura em 24 h e licenças vigentes com uso comercial e redistribuição. Entretanto:

- não valida proprietário institucional, apesar do comentário/configuração afirmar isso;
- não produz artefato versionado, hash ou lista completa auditável;
- a alegação “0 de 113” está apenas em comentário e HTML;
- o runtime [`openaq.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/server/src/live/openaq.ts) revalida mobile/monitor/licença, mas não a recência de 24 h;
- `dateTo===null` é usado como única definição de licença vigente; `dateFrom` não é modelado.

A quantidade de 113 e a seleção de oito localizações dos EUA são **não verificáveis a partir dos artefatos versionados**. A API exige chave e nenhuma credencial foi usada na auditoria.

### 5.2 ONS

O adaptador lê 8.192 bytes finais do CSV anual, toma a última linha SIN pela ordem física e publica CC BY 4.0. A chamada GET independente encontrou:

```text
bucket efetivo: endpoint S3 us-west-2
última linha SIN na cauda: 2026-11-01 23:00:00 BRT
corte da auditoria: 2026-11-03 15:12 UTC
```

Isso revela duas divergências:

1. O [registro Open Data](https://github.com/awslabs/open-data-registry/blob/main/datasets/ons-opendata-portal.yaml) indica `sa-east-1`, mas o S3 retornou `PermanentRedirect` para `s3-us-west-2`; o código trata o redirect, portanto continua funcional, mas não há co-localização regional real confirmada.
2. A leitura mais recente estava cerca de 61 horas antiga em UTC. O adaptador não rejeita dado antigo, e o painel usa `completedAt` do job para “desatualizado”.

Outros riscos:

- a última linha física pode não ser o maior timestamp;
- se o servidor ignorar Range e responder 200, o código aceita e baixa o arquivo completo;
- os 8.192 bytes são uma hipótese operacional;
- faltas de colunas/séries são silenciosas;
- a conversão fixa UTC−3 precisa acompanhar o contrato da fonte.

### 5.3 Idempotência, concorrência e atomicidade

`LiveRun.slotUtc @unique` bloqueia duplicação concorrente. Porém:

- `opts.slot` explícito não é arredondado para cinco minutos;
- run morto em `running` nunca libera ou expira;
- run `failed` ocupa o slot para sempre;
- um retry do Scheduler pode receber `slot_ocupado` e o CLI retornar zero;
- criação do run, inserção de observações e atualização final não são uma transação;
- `firstRunId` não é chave estrangeira;
- correções da fonte para o mesmo sensor/timestamp são descartadas por `skipDuplicates`;
- `sources=['openaq','ons']` registra intenção, não sucesso efetivo.

### 5.4 Normalização e saturação

As faixas são declaradas por parâmetro e a amplitude usa `0,1+0,9x`. Valores fora da faixa são saturados e marcados `clipped`. Pontos corretos:

- valor original permanece no banco;
- canal ausente não desloca outros canais;
- unidade desconhecida exclui o valor do quadro;
- ruído tem seed persistida.

Limites:

- igualdade textual de unidade é frágil;
- run pode ser `succeeded` mesmo que nenhuma observação seja normalizável;
- o valor recuperado saturado representa o limite declarado, não o valor original;
- as faixas são escolhas de produto, não calibração física do protocolo.

### 5.5 API e painel

A rota pública tem whitelist de assets, valida janela/série, limita a 1.000 pontos e não retorna coordenadas. Isso está bem delimitado.

As inconsistências substantivas são:

- staleness usa conclusão do job e não `observedAt`;
- as últimas leituras são consultadas separadamente do último run com protocolo;
- o frontend combina por chave sem exigir mesmo slot/run;
- as consultas do resumo não usam snapshot/transação e podem montar resposta híbrida durante ingestão;
- `/api/live/public` é aberta no runtime, mas não declara `security: []` apesar da segurança OpenAPI global.

## 6. PR #54, separado do baseline

O PR altera somente HTML/CSS/JS do painel e não muda banco, API ou DSP. Seus principais ganhos:

- separa cobertura, detecção, fidelidade e canal simulado;
- explica que o sweep usa quadros sintéticos, não leituras reais;
- rebaixa “linha de base MQTT” para estimativa de tamanho;
- esclarece que 0/113 significa reprovação no filtro, não ausência de medições brasileiras.

### Métrica ±2%

O código calcula:

```text
|amplitudeRecebida - amplitudeEnviada| / 0,9 <= 0,02
```

Como `A=0,1+0,9(v-vmin)/(vmax-vmin)`, para valor não saturado isso equivale exatamente a erro menor ou igual a 2% da faixa declarada. A definição é matematicamente coerente **condicionada a canal detectado e não saturado**.

Problemas restantes:

- `comValor` inclui canais saturados; nesse caso mede fidelidade à amplitude truncada, não ao valor original;
- canais não detectados ficam fora do denominador; a separação visual de recall reduz, mas não elimina, o risco de leitura otimista;
- a métrica é calculada no navegador e não possui teste dedicado no PR;
- a correspondência temporal do `main` entre leitura e run permanece.

**Parecer do PR:** melhoria de comunicação, recomendável com ajuste do denominador para `presente && !clipped` ou rótulo explícito “entre valores detectados, em relação à amplitude transmitida”. Não altera o diagnóstico de maturidade.

## 7. Segurança

### 7.1 Segurança efetiva da API

Confirmado:

- chaves aleatórias de 32 bytes;
- armazenamento de SHA-256 e prefixo;
- comparação constante;
- expiração, revogação e escopos;
- `x-api-key` ou Bearer;
- CLI evita stdout em produção e revoga chave se gravação no Secrets Manager falhar;
- Helmet, CORS explícito, RDS privado e OIDC.

Parcial:

- bearer é replayável enquanto válido;
- não há tenant/owner por dispositivo;
- não há rate limit, WAF ou quotas no app;
- `lastUsedAt` é atualização assíncrona, não trilha de auditoria;
- a rota pública Live faz várias consultas ao RDS, embora cacheadas.

### 7.2 HSL

[`hsl_auth.py`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/71fb8ea03241f48d1a63e3cc356ae07c8e094948/security/hsl_auth.py#L89-L182) não usa fase física. A assinatura é `SHA256(challenge_hash + ':' + secret)`, chamada no comentário de “HMAC-like”, em vez da construção HMAC padronizada. [FIPS 198-1](https://csrc.nist.gov/csrc/media/publications/fips/198/1/final/documents/fips-198-1_final.pdf)

Falhas demonstráveis no código:

- desafio não é consumido após sucesso; a resposta pode ser repetida durante `max_age`;
- `verify_response` chama `generate_response`, que cria sessão como efeito colateral;
- comparação da assinatura é string comum;
- resposta serializada inclui os primeiros 16 bytes da `session_key`;
- não há cifra, AEAD, KEM, assinatura digital ou forward secrecy;
- módulo não protege a API.

Logo, replay, confidencialidade, ML-KEM/ML-DSA e “assinatura timbral” não são demonstrados.

### 7.3 LFSR e detector de intrusão

O LFSR tem 8/16/32 bits, seed padrão e evolução determinística. Hash do estado não aumenta a entropia. É adequado como visualização/sequência, não geração ou rotação criptográfica.

O detector recebe fases já calculadas pelo chamador; canal ausente assume a fase esperada e passa. Não há RF, aquisição, baseline de canal, ROC/FAR/FRR ou modelo adversarial. Ele demonstra uma regra de limiar, não detecção de intrusão operacional.

### 7.4 Dependências

Versões travadas no `main`:

```text
fastify 5.12.8
zod 3.25.76
@fastify/swagger-ui 6.1.2
@fastify/static 10.1.8
```

`npm audit --omit=dev` encontrou:

- 1 HIGH: Zod [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), acúmulo de erros e consumo de memória em coleções grandes;
- 4 moderados em Swagger UI/static/glob/minimatch.

A condição Zod existe parcialmente em `POST /api/devices/register`: `sensors` e `capabilities` são arrays sem limite Zod ou `maxItems`. A rota exige `devices:write` e o Fastify possui limite de corpo, reduzindo o impacto; ainda é um caminho autenticado para consumo excessivo. Não foi executada prova de exaustão.

## 8. Engenharia e infraestrutura

### 8.1 CI real

O API CI é a automação mais confiável: lockfile, Prisma, fixtures, typecheck, Vitest, build, migração, drift, smoke auth, imagens, smoke da migração e Trivy.

O estado global não é verde:

- `cppcheck --enable=all --error-exitcode=1` falha por funções não usadas;
- Markdown falha em violações já existentes;
- setup C++ falhou por DNS `apt.llvm.org`;
- TruffleHog em push usa `base=main`, `head=HEAD`, ambos iguais;
- License Compliance espera copyright de 2024 e uma licença diferente da documentação atual;
- upload SARIF falha sem permissões `security-events` adequadas.

Workflows de performance e segurança avançada estão desabilitados. O de performance parte da raiz sem `package.json` e referencia caminhos/scripts inexistentes; não é evidência de performance.

### 8.2 Docker e supply chain

Pontos positivos: multi-stage, `npm ci`, runtime sem devDependencies, usuário não root e imagem separada de migração.

Lacunas: imagens base por tag mutável, Actions por major/branch (`@master`, `@main`, `@v1`), sem SBOM, assinatura ou provenance verificada. O GitHub documenta que referências imutáveis reduzem risco de supply chain. [Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)

### 8.3 AWS

Confirmado em definição:

- GitHub OIDC restrito ao environment;
- Secrets Manager para banco e OpenAQ;
- RDS PostgreSQL privado, cifrado, backup 7 dias, deletion protection;
- ECR scan-on-push;
- migração antes da API;
- readiness após deploy.

Confirmado em execução: o deploy do baseline passou todos esses passos observáveis no workflow. Estado real de políticas, banco e schedule não foi consultado.

Limites:

- RDS Single-AZ é ponto único de falha aceitável para POC, não alta disponibilidade;
- tarefas públicas recebem IPv4;
- SG da task aceita porta 3001 de todo CIDR da VPC, mais amplo que “somente SG do ALB”;
- papel GitHub usa `ecs:*` em `Resource:*`;
- o script base dá acesso apenas ao segredo do banco; o script separado de agenda amplia para OpenAQ. Reexecutar só a infraestrutura base pode remover o acesso OpenAQ;
- criar a agenda sem argumento sempre a deixa `DISABLED`, inclusive se já estivesse ligada;
- deploy registra a task Live, mas não testa o job ou `/live` e não habilita schedule.

### 8.4 Custo

A arquitetura lean é coerente: uma API contínua já existente e tarefa Live efêmera. A estimativa cobre as categorias principais, mas depende de premissas de LCU, logs, ECR e tráfego. Não há saída versionada do cálculo atual; “US$55” é comentário, não evidência de fatura.

## 9. Integridade das alegações

| Alegação pública | Classificação | Fundamento |
|---|---|---|
| API funciona e tem auth por escopo | Demonstrada | Código, testes e deploy. |
| H16 possui 80 canais | Contradita | A definição/código enumeram 159. |
| Ortogonalidade matematicamente garantida | Contradita nas condições atuais | Cinco canais fora de bin; não há sincronização/canal. |
| Interferência zero | Não demonstrada | Há leakage, correlação cruzada e nenhum ensaio físico. |
| 50–65% menos energia | Não demonstrada | Nenhuma medição energética ou comparação mesma camada/hardware. |
| Qualquer hardware | Não demonstrada | Frequência/taxa já impõem DAC/ADC e front-end; não há port ARM/ESP32 validado. |
| Escalabilidade infinita / 1.000+ canais | Contradita pela implementação | 12 canais HPM, 32 razões por chamada e banda/período finitos. |
| Sincronização nativa sem negociação | Não demonstrada | Não há aquisição de quadro, CFO/SFO ou estimador. |
| HSL impede replay | Contradita | Desafio não é consumido. |
| HSL/PQC/confidencialidade | Não demonstrada | Sem KEM, assinatura, cifra ou integração. |
| Pesquisa revisada por pares no Zenodo | Não verificada e não sustentada pelo meio | DOI/Zenodo torna artefato citável; Zenodo não exige peer review. [Zenodo](https://about.zenodo.org/) |
| Nautam Live usa dados reais | Parcial | Código coleta fontes reais; testes usam fakes e operação da agenda/RDS não foi verificada. |
| MQTT baseline prova eficiência | Não demonstrada | É estimativa de bytes de representação e exclui PHY/transporte/energia. PR #54 melhora o texto. |

## 10. Síntese técnica

O núcleo útil do projeto é uma implementação reproduzível de sinal multitone esparso com doze amplitudes, acompanhada de uma boa demonstração web e pipeline cloud. O maior risco científico é confundir a elegância de razões racionais com propriedades de enlace que dependem de janela, relógio, canal e hardware. O maior risco de engenharia é a divergência entre resultados do run e dados exibidos. O maior risco público é a distância entre alegações e evidência.

Conteúdo externo foi resumido e reformulado para conformidade com restrições de licenciamento.