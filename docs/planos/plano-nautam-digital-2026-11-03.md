# Plano: Nautam totalmente digital e sem dados simulados em produção

Versão para aprovação da Luna · 03/11/2026 · baseline `main@7ec77b6` + PR #56 (Zod)

Este plano substitui integralmente o plano anterior de bancada física, que foi descartado por violar as condições reais da Hubstry. Essas condições agora estão registradas em `.kiro/steering/hubstry-condicoes-reais.md`, arquivo que todo agente lê antes de propor qualquer coisa. Em resumo: fundador solo, bootstrap, sem compra de hardware, créditos AWS (Amazon Web Services) disponíveis, entregas em horas ou poucos dias.

## 1. Objetivo

O objetivo é que o painel público do Nautam Live deixe de exibir qualquer elemento sintético. Hoje os dados são reais, mas o sinal é descartado na memória e o ruído é gerado por software. Ao fim deste plano, os três elementos passam a ser reais ou artefatos reais publicados:

| Elemento | Hoje | Ao fim do plano |
|---|---|---|
| Dados | Reais (OpenAQ e ONS) | Reais, com idade e correspondência por execução |
| Sinal | Calculado e descartado | Forma de onda digital real, publicada como arquivo verificável |
| Ruído | AWGN (Additive White Gaussian Noise, ruído gaussiano branco aditivo) gerado pelo código | Ruído real gravado de receptores públicos de rádio, com atribuição |
| Canal | Emulado | Continua emulado, e o painel declara isso |

A analogia de referência é o sintetizador digital usado em produção musical. Ele gera a onda inteiramente em software, e essa onda é real como arquivo, ainda que nenhum circuito analógico participe da geração. O Nautam passa a ser tratado como rádio definido por software nesse sentido: toda a modulação e a demodulação acontecem em código.

## 2. Limite de maturidade, declarado de antemão

Sem caminho físico, o plano consolida o TRL (Technology Readiness Level, nível de maturidade tecnológica) 3 da camada digital, isto é, a prova de conceito experimental com evidência reprodutível. Ele não declara TRL 4 nem superior. A validação física fica registrada como condição externa futura: ela depende de receita, parceiro, edital ou cliente que forneça equipamento. Por conseguinte, o horizonte comercial deste plano é a prontidão para piloto com parceiro que disponha de hardware, e não go-to-market de um rádio.

## 3. O que se aproveita da revisão da Luna ao plano anterior

| Ponto da Luna | Como entra aqui |
|---|---|
| Perfil 48 kHz / 480 amostras / f0 6 kHz / Δf 100 Hz | Adotado como perfil digital novo. 48 kHz é taxa padrão de áudio, de modo que o arquivo toca em qualquer dispositivo. O HPM 1.0 não é alterado |
| Goertzel para os 12 bins conhecidos | Adotado. A FFT (Fast Fourier Transform, transformada rápida de Fourier) completa fica para diagnóstico e para o decodificador cego |
| Especificar o quadro antes de medir BER | Adotado como Entrega 2 |
| Carga PRBS para medir erro de bit | Adotado. PRBS (Pseudo-Random Binary Sequence, sequência binária pseudoaleatória) é uma sequência de teste conhecida pelos dois lados |
| Taxonomia de erros | Adotada: erro de bit, quadro rejeitado pelo CRC, quadro perdido, quadro duplicado, valor recuperado com erro, falha de sincronização |
| Headroom, fator de crista e clipping | Adotados no domínio digital: a soma dos 12 tons não pode saturar o PCM (Pulse-Code Modulation, modulação por código de pulso) de 16 bits |
| Retenção definida no S3 | Adotada: artefatos por execução com retenção de 30 dias |
| Rigor de TRL e "piloto" em vez de "go-to-market" | Adotado na seção 2 |
| D1, D2, D3 | Mantidos: painel atual rotulado até a troca; H16 com 159; licença decidida pelo Guilherme |
| Hardware, bancada, energia física, IoT Core, Greengrass, RF, D4 e D5 | Descartados por violarem as condições reais |

## 4. Entregas (cada uma é um PR pequeno, em produção logo após o merge)

### Entrega 1 — Perfil digital coerente e receptor Goertzel (1 a 2 dias)

- Perfil novo `HPM-D48`: taxa de amostragem de 48.000 Hz, 480 amostras por quadro (10 ms), f0 de 6.000 Hz e resolução de 100 Hz. Todos os 12 canais caem em bins inteiros, porque f0 / Δf = 60 e todos os denominadores da tabela HPM dividem 60.
- Receptor HPM com o algoritmo de Goertzel, que calcula só os 12 bins necessários, com custo proporcional a 12 × 480 operações.
- Escala global com margem de pico: o fator de crista do quadro é medido e publicado, e um teste garante ausência de clipping em PCM de 16 bits.
- Correção de `cardinality_hn()` para 159 e documentação da definição retangular de H16.
- Testes: recuperação simultânea, variação de fase, amplitudes desiguais e correlação cruzada entre tons próxima do erro de máquina.

### Entrega 2 — Quadro binário especificado (2 dias)

Hoje o Nautam atribui amplitudes contínuas a 12 canais; não há bits, de modo que BER (Bit Error Rate, taxa de erro de bits) não pode ser medida. Esta entrega cria a camada que faltava:

- **Símbolo:** cada símbolo de 10 ms carrega 2 bits por canal, codificados em 4 níveis de amplitude. São, portanto, 24 bits por símbolo, ou 2.400 bits por segundo brutos.
- **Quadro:** preâmbulo de sincronização fixo; cabeçalho com versão, perfil, número de sequência e tamanho; payload; CRC-16 (Cyclic Redundancy Check, verificação cíclica de redundância) ao final.
- **Payload real:** as 12 leituras quantizadas em 16 bits cada, com a faixa declarada de cada série (a mesma de hoje).
- **Payload de teste:** quadros PRBS-9 transmitidos em paralelo a cada execução, para medir BER independentemente da cadência das fontes ambientais.
- A especificação do quadro fica versionada em `docs/` antes do código.

### Entrega 3 — Forma de onda real publicada (1 dia)

- Cada execução grava no S3 o arquivo WAV (48 kHz, 16 bits, mono) do quadro transmitido e do quadro recebido, com um manifesto JSON que traz o hash SHA-256, o perfil, a sequência e o `runId`.
- O painel exibe o link do arquivo. Qualquer pessoa pode baixar, ouvir, abrir num software de áudio e decodificar com o código aberto.
- Volume estimado: cerca de 12 execuções por hora, com poucos kilobytes cada, o que dá dezenas de megabytes por mês. A regra de ciclo de vida apaga os arquivos após 30 dias.

### Entrega 4 — Ruído real no lugar do ruído sintético (2 a 3 dias, com etapa de viabilidade)

**Etapa de viabilidade, antes de qualquer código:** verificar três condições em fontes públicas de gravação de rádio, como a rede KiwiSDR de receptores SDR (Software Defined Radio, rádio definido por software) abertos na internet.

1. Os termos de uso permitem captura automatizada esporádica e redistribuição com atribuição?
2. A largura de banda capturável cobre o perfil de 48 kHz, diretamente ou por reamostragem documentada?
3. A captura funciona a partir da tarefa ECS na AWS?

**Se as três forem atendidas:** uma captura curta por dia (por exemplo, 10 segundos de ruído de fundo) é armazenada no S3 com atribuição e metadados de origem. A cada execução, um trecho dessa gravação é somado digitalmente ao sinal, e a SNR (Signal-to-Noise Ratio, relação sinal-ruído) é medida, não imposta. O AWGN sai da produção e fica só no CI (Continuous Integration, integração contínua).

**Se alguma falhar:** busca-se um conjunto público de gravações reais de ruído com licença compatível. Se nenhum servir, o AWGN permanece, rotulado como sintético, e o painel continua declarando isso. O plano não esconde a falha.

### Entrega 5 — Pendências P1 (1 a 2 dias)

- Idade máxima por leitura nos adaptadores OpenAQ e ONS, com a idade exibida no painel.
- Valor original e valor recuperado vindos do mesmo `runId`.
- Workflows: TruffleHog (BASE igual a HEAD), permissão do upload SARIF, verificador de licença, Markdownlint e Cppcheck.
- Licença do código alinhada à decisão D3.

## 5. Critérios de aceite propostos (congelados antes da Entrega 4)

| Métrica | Limite proposto |
|---|---|
| BER com PRBS-9, ruído real, SNR medida ≥ 20 dB | ≤ 10⁻⁴ |
| Quadros rejeitados pelo CRC | ≤ 1% |
| Quadros perdidos ou duplicados (pela sequência) | 0 em 24 horas |
| Clipping no PCM de 16 bits | 0 ocorrências |
| Correlação cruzada máxima entre tons, sem ruído | < 10⁻¹⁰ |
| Tempo de CPU do receptor por quadro, p95 | Publicado; sem limite nesta fase |

Os números de BER e CRC são propostas iniciais. Se a Luna preferir outros, eles são ajustados antes da Entrega 4, nunca depois de ver os resultados.

## 6. Custo

O custo incremental estimado é inferior a US$ 1 por mês: armazenamento S3 de poucas dezenas de megabytes e a mesma tarefa ECS agendada que já roda. Não há compra de equipamento nem serviço novo.

## 7. Painel público ao fim do plano

A declaração do painel muda de "simulação de sinal com dados reais; energia e interferência em campo não medidas" para:

"forma de onda digital real com dados reais e ruído real gravado; canal emulado em software; transmissão física, energia e interferência em campo não medidas"

## 8. Decisões pendentes com o Guilherme

- **D3, licença do código.** As opções são uma licença proprietária com o repositório como vitrine; a BSL (Business Source License, licença de código-fonte disponível com uso comercial sob contrato); ou dupla licença. A escolha é estratégica e jurídica, e não deve ser feita só para o workflow passar.

As demais decisões do plano anterior estão resolvidas: D1, painel atual rotulado até a troca; D2, H16 com 159. D4 e D5 foram eliminadas.
