# Parecer executivo — Nautam IoT Protocol

**Data de corte:** 03/11/2026, 15:12 UTC
**Baseline do produto:** [`main@71fb8ea03241f48d1a63e3cc356ae07c8e094948`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/tree/71fb8ea03241f48d1a63e3cc356ae07c8e094948)
**Alteração pendente, avaliada separadamente:** [PR #54](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/54), `7bf50e2e22d76981fa627ea60bc7c90b532858a5`
**Decisão:** **CONDITIONAL GO** para a próxima validação experimental; **NO-GO** para alegações de protocolo físico maduro, ganho energético, interferência zero ou segurança intrínseca.

## 1. Situação congelada

| Item | Estado verificado |
|---|---|
| Checkout local | `spec/nautam-live@ba0eb1a4107a839e8a08c58894064903aa4349e5`; working tree limpo antes da auditoria. O checkout não foi usado como baseline. |
| `origin/main` | `71fb8ea03241f48d1a63e3cc356ae07c8e094948`, merge do [PR #53](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/53), painel E3. |
| PRs abertos | Somente [PR #54](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/54), três arquivos estáticos do painel, sem revisão registrada no instante do corte. |
| API CI do `main` | [Run 41658832142](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658832142): sucesso nos dois jobs. |
| Deploy do `main` | [Run 41658882442](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658882442): sucesso, inclusive migração, registro da task Live, atualização ECS e `/api/readyz`. Isso não prova execução da agenda Live. |
| CI geral do `main` | [Run 41658832246](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658832246): falhou em análise estática, Markdown, setup C++ e upload SARIF. |
| Security Checks do `main` | [Run 41658831810](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41658831810): falhou por configuração de TruffleHog, copyright esperado e permissão de upload SARIF. |
| PR #54 | API CI passou; CI geral e License Compliance falharam por problemas preexistentes; CodeQL ficou neutro e Trivy passou. |
| Aplicação pública | As URLs informadas retornaram HTTP 403 no proxy desta auditoria. O estado publicado além do readiness do deploy é **não verificado**. |
| Teste local independente | Em uma cópia descartável de `origin/main`: `npm ci`, typecheck, 72/72 testes Vitest e build passaram. O `npm audit --omit=dev` encontrou cinco avisos de produção: quatro moderados e um alto. |

## 2. O que o Nautam é hoje

O produto incorporado em `main` contém três partes de maturidade muito diferente:

1. **Serviço de software funcional:** API Fastify, PostgreSQL/Prisma, autenticação por API key e escopo, imagens Docker, migração, OIDC e deployment ECS. Essa parte compila, passa a suíte API e foi implantada com readiness bem-sucedido.
2. **Modelo de sinalização multitone funcional em simulação:** doze frequências HPM fixas, amplitudes derivadas de valores numéricos, soma de senóides, AWGN determinístico e detecção por magnitude FFT/DFT. É melhor descrito como **modulação vetorial de amplitude sobre uma base multitone esparsa**.
3. **Protocolo físico e segurança harmônica aspiracionais:** não há transmissor/receptor RF, preâmbulo, enquadramento, sincronização, estimação de canal, correção de clock/CFO/SFO, CRC/FEC, MAC, BER/PER, link budget ou energia medida. HSL/LFSR/detecção por fase são demonstrações Python não integradas à API e não constituem controles criptográficos do serviço.

O Nautam Live implementa o fluxo **fonte pública → coleta → normalização → sinal sintético → AWGN → receptor → métricas → banco → painel**. Os valores de entrada são reais quando as fontes respondem; o enlace inteiro permanece simulado.

## 3. Principais conclusões

### Conclusão matemática

A definição implementada é

\[
H_N=\{a/b:1\le a,b\le N,\gcd(a,b)=1\}.
\]

Para essa região quadrada,

\[
|H_N|=2\sum_{k=1}^{N}\varphi(k)-1.
\]

Em `N=16`, o resultado é **159**, confirmado por enumeração independente e pelo porte TypeScript. O README e os núcleos HALE/HPG Python usam `Σφ=80`, fórmula de outra região de frações, e portanto contradizem o conjunto que enumeram. A Omnigrid resultante teria 318 pares com polaridade, não 160.

As razões racionais permitem uma janela comum, mas **não garantem ortogonalidade em qualquer janela**. Para os denominadores HPM `{1,2,3,4,5}`, a janela coerente mínima é

\[
T=\operatorname{lcm}(1,2,3,4,5)/f_0=60/16384=3{,}662109375\,ms,
\]

ou 480 amostras a 131.072 Hz. O quadro atual usa `T=1/64 s`, 2.048 amostras. Cinco tons não caem em bins inteiros. O cálculo independente mediu correlação cruzada normalizada máxima de **0,006509** no quadro atual e aproximadamente `5,3×10⁻¹⁵` na janela coerente. A separação HPM continua larga, então a detecção pode funcionar; a alegação de ortogonalidade garantida, contudo, não é válida para a configuração atual.

### Conclusão experimental

Os testes demonstram:

- paridade Python/TypeScript nos nove vetores determinísticos versionados;
- recuperação de presença dos 12 canais no cenário ideal coberto;
- amplitude aproximada no receptor conhecido, com erro residual admitido pelo teste;
- repetibilidade de AWGN com semente;
- comportamento exploratório em sete SNRs e 20 quadros por SNR;
- transformação de objetos no formato das fontes reais.

Eles não demonstram:

- correção independente do oráculo Python;
- recuperação de payload binário, fase ou amplitude física absoluta;
- BER, PER, alcance, energia, coexistência, sincronização ou rádio;
- robustez a CFO/SFO, multipercurso, Doppler, ruído colorido/impulsivo, near-far, clipping analógico ou intermodulação;
- suficiência estatística para os limiares publicados.

### Conclusão do Nautam Live

O código E1/E2/E3 está presente e integrado. Há, porém, quatro limitações substantivas:

1. O runtime OpenAQ não repete a condição de “leitura nas últimas 24 h” usada na qualificação.
2. A atualidade pública é calculada pelo fim do job, não pelo timestamp da medição. Em GET público durante a auditoria, a cauda ONS mais recente era de **01/11/2026 23:00 BRT**, enquanto o corte era 03/11/2026; o painel poderia rotular um job novo sobre dado antigo como “normal”.
3. Um slot criado e interrompido fica `running` para sempre; retries retornam `slot_ocupado`, inclusive após falha, e podem mascarar recuperação.
4. O resumo combina as últimas leituras de cada série com o último run que contém protocolo, sem garantir que “original” e “recuperado” pertençam ao mesmo quadro.

## 4. Maturidade tecnológica

A avaliação usa a escala NASA TRL, que distingue conceito, prova analítica/experimental e validação em ambiente. A própria orientação NASA recomenda avaliar componentes separadamente e limita a maturidade de um conjunto pelo componente menos maduro. [NASA TRL](https://esto.nasa.gov/trl/) · [TRL 3–4](https://www.nasa.gov/pdf/458490main_TRL_Definitions.pdf)

| Dimensão | TRL | Justificativa |
|---|---:|---|
| Matemática | **2–3** | Conceito formalizado e simulado, mas cardinalidade é inconsistente e as condições de ortogonalidade não são satisfeitas pelo quadro atual. |
| Algoritmo DSP | **3** | Síntese, FFT e detector funcionam em simulação; faltam sincronização, canal, offset e validação independente. |
| Software/API | **5** | Componentes integrados, testados localmente e implantados em cloud; disponibilidade pública completa não pôde ser inspecionada. |
| Experimento | **3** | Prova de conceito em software com AWGN; nenhuma validação física. |
| Hardware | **1** | Nenhum protótipo de transmissor/receptor ou aquisição física identificado. |
| Integração cloud/Live | **4–5** | Pipeline, banco, API e painel integrados; agenda e dados reais em produção não foram verificados. |
| Aplicação como protocolo IoT | **2** | Aplicação formulada, mas PHY/MAC, framing e interoperabilidade não existem. |

**TRL global da tecnologia de comunicação: 2–3.** O TRL 5 do serviço web não eleva o protocolo físico.

## 5. Respostas obrigatórias

1. **O Nautam funciona como software?** Sim. API, pipeline Live e simulação compilam e passam 72 testes; o deploy do baseline concluiu com readiness.
2. **O núcleo matemático está correto nas condições implementadas?** Parcialmente. A síntese e frequências são consistentes; a cardinalidade Python/README está errada e a janela Live não é coerente para cinco canais.
3. **Existe um protocolo efetivamente implementado?** Existe um modelo de sinalização e uma aplicação web. Não existe ainda um protocolo físico completo ou uma pilha IoT interoperável.
4. **O receptor recupera corretamente os dados?** Recupera presença de canais e aproxima amplitudes no cenário ideal/sintético. Não recupera payload binário, fase nem valor físico após um canal real desconhecido.
5. **Os resultados são reproduzíveis?** Sim para seeds, fixtures e versão auditada; não há campanha externa independente ou artefatos de execução física.
6. **A simulação representa adequadamente a hipótese?** Representa o caso restrito de relógios perfeitos, fase fixa e AWGN. Não representa adequadamente um enlace real.
7. **Há contribuição técnica relevante?** Há uma integração concreta de uma tabela racional, mapeamento de grandezas e demonstração reproduzível. Os blocos fundamentais são técnicas conhecidas; novidade científica ou vantagem não foi demonstrada.
8. **O Live demonstra além de simulação alimentada por dados reais?** Não quanto à comunicação. Ele demonstra engenharia de ingestão, proveniência, persistência e apresentação.
9. **Há evidência para avançar a experimento físico?** Sim, como experimento barato e falsificável, após P0. Não há evidência para produto RF ou comparação energética.
10. **Pode apresentar-se publicamente como tecnologia em desenvolvimento?** Sim, se remover garantias e usar “arquitetura experimental/prova de conceito multitone”.
11. **Três bloqueios principais:** definição/cardinalidade e janela; ausência de receptor físico/sincronização/canal; alegações e segurança muito acima da evidência.
12. **Experimento de maior valor por menor custo:** loopback baseband com DAC e ADC de relógios independentes a 192 kHz, atenuador e ruído controlado, comparando quadro atual e janela coerente; depois repetir em SDR se o resultado justificar.

## 6. Decisão

### CONDITIONAL GO

É tecnicamente justificável avançar para **uma validação física de laboratório pequena**, não para ampliar a plataforma ou declarar protocolo pronto. As condições são:

1. corrigir a definição e cardinalidade H16/Omnigrid em código, README e métricas;
2. escolher e documentar uma janela coerente ou declarar explicitamente a não ortogonalidade;
3. alinhar o painel pelo mesmo `runId` e medir atualidade pelo timestamp da fonte;
4. remover ou qualificar “zero interference”, “50–65% menos energia”, “infinitamente escalável”, “qualquer hardware”, “segurança intrínseca” e “peer-reviewed”;
5. definir o experimento antes de coletar resultados, com métricas, seeds, número de repetições e dados brutos versionados.

O avanço proposto é **GO para produzir evidência** e **NO-GO para ampliar promessas**.

## 7. Experimento recomendado

### Loopback multitone com relógios independentes

- **TX:** gerar quadros HPM em 192 kHz por DAC ou interface de áudio.
- **Canal:** cabo, atenuador, combinação passiva e gerador de ruído; opcionalmente filtros e não linearidade controlada.
- **RX:** segunda interface/ADC com clock independente.
- **Condições:** quadro atual versus 480 amostras coerentes; CFO/SFO medido; fases aleatórias; níveis near-far; AWGN e interferidor estreito; 12 tons e subconjuntos.
- **Métricas:** recall/precisão, erro de amplitude normalizada, falso pico/quadro, SNR medida, CFO/SFO, EVM ou NMSE, PAPR e latência de CPU. BER/PER somente após definir símbolos, framing e CRC.
- **Amostragem mínima:** pelo menos 1.000 quadros independentes por condição para taxas percentuais, com intervalo de confiança binomial; aumentar quando o alvo de erro for inferior a 1%.
- **Custo:** baixo se interfaces existentes suportarem 192 kHz; não requer cloud nova. O objetivo é decidir se vale migrar para SDR/RF.

## 8. Limitações desta auditoria

- O proxy bloqueou a URL pública da API e os registros Zenodo/DOI; esses itens estão marcados como não verificados.
- Nenhuma credencial, AWS API, banco de produção ou segredo foi consultado.
- O deploy bem-sucedido prova criação/atualização e readiness, não agenda habilitada, ingestões Live ou conteúdo do RDS.
- A revisão de estado da arte não é busca jurídica de anterioridade ou liberdade de operação.

Conteúdo externo foi resumido e reformulado para conformidade com restrições de licenciamento.