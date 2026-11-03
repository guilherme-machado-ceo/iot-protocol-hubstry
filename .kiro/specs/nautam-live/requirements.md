# Documento de Requisitos — Nautam Live

## Introdução

O Nautam Live deve demonstrar o protocolo Nautam com medições ambientais reais e públicas. A cada cinco minutos, uma tarefa efêmera deve buscar até 12 leituras elegíveis, representá-las nos 12 canais HPM 1.0 do conjunto H16, sintetizar um sinal com ruído controlado, decodificá-lo por FFT e publicar resultados verificáveis em um painel público.

O MVP é uma demonstração de software. Ele não mede propagação de rádio, interferência eletromagnética ou consumo de energia em campo. A arquitetura deve reutilizar a API Fastify, o núcleo H16 em TypeScript, o RDS PostgreSQL, o ECR, o ECS/Fargate e o workflow de produção existentes.

## Glossário

- **Nautam_Live**: demonstração pública que combina medições reais com transmissão e decodificação simuladas.
- **Fonte_Inicial**: OpenAQ API v3, sujeita à qualificação de licença, atualidade e ausência de dados pessoais.
- **Fonte_Reserva**: portal de dados abertos do ONS no bucket S3 público em `sa-east-1`, usado quando a Fonte_Inicial estiver indisponível ou inelegível.
- **Observação**: valor medido por um sensor, com unidade, parâmetro, instante da medição e proveniência.
- **Execução**: ciclo lógico de ingestão, codificação, síntese, decodificação, cálculo de métricas e persistência.
- **H16**: conjunto das 159 razões irredutíveis `a/b`, com `a,b ≤ 16`, já implementado na API.
- **HPM_1_0**: tabela existente de 12 canais do Nautam, usando `f0 = 16.384 Hz`.
- **Sinal_Simulado**: vetor de amostras produzido por composição harmônica em software, com ruído pseudoaleatório controlado.
- **Linha_Base_MQTT**: cálculo analítico dos bytes de uma publicação MQTT 3.1.1 para a mesma carga útil lógica; não é uma medição de rede.
- **Painel_Publico**: página HTML pública, servida pela aplicação existente, que apresenta dados previamente selecionados e métricas do Nautam Live.
- **Dado_Elegivel**: dado de estação institucional e fixa, sem identificador de pessoa natural e com licença que permita exibição pública e uso comercial.

## Requisitos

### Requisito 1 — Qualificação das fontes públicas

**História de usuário:** Como responsável pelo produto, quero usar apenas fontes verificáveis e licenciadas, para que a demonstração possa ser exibida publicamente sem assumir direitos inexistentes.

#### Critérios de aceitação

1.1. O SISTEMA DEVE usar OpenAQ API v3 como Fonte_Inicial e o portal de dados abertos do ONS como Fonte_Reserva.

1.2. QUANDO uma localização da OpenAQ for considerada, O SISTEMA DEVE aceitar somente licença com `commercialUseAllowed = true`, redistribuição permitida e atribuição disponível.

1.3. QUANDO o proprietário de uma localização puder ser uma pessoa física, a localização for móvel ou a licença não estiver determinada, O SISTEMA DEVE rejeitar a localização.

1.4. O SISTEMA DEVE persistir, junto de cada observação, provedor, identificador institucional da estação ou série, parâmetro, unidade, instante observado, licença, atribuição e URL da fonte.

1.5. SE a Fonte_Inicial falhar, responder com limitação de taxa ou não fornecer ao menos uma observação nova e elegível, ENTÃO O SISTEMA DEVE tentar a Fonte_Reserva, preservando a cadência e o instante reais informados por ela.

1.6. O SISTEMA NÃO DEVE apresentar uma observação antiga ou repetida como se tivesse sido produzida no instante da ingestão.

1.7. O SISTEMA NÃO DEVE ativar outra fonte pesquisada sem que endpoint, autenticação, limite de taxa, licença de exibição pública/comercial e risco de dado pessoal tenham sido confirmados.

### Requisito 2 — Ingestão agendada e idempotente

**História de usuário:** Como operador solo, quero uma ingestão autônoma e barata, para manter a demonstração atualizada sem servidor adicional permanente.

#### Critérios de aceitação

2.1. O EventBridge Scheduler DEVE solicitar uma tarefa ECS/Fargate avulsa a cada cinco minutos em `sa-east-1`.

2.2. QUANDO uma tarefa iniciar, O SISTEMA DEVE atribuir a execução ao intervalo UTC de cinco minutos correspondente.

2.3. SE o Scheduler repetir a entrega ou duas tarefas se sobrepuserem, ENTÃO O SISTEMA DEVE produzir no máximo uma execução bem-sucedida por intervalo, usando restrição única no banco e operação idempotente.

2.4. O SISTEMA DEVE aplicar timeout HTTP, no máximo duas novas tentativas com atraso e tratamento explícito de respostas `429` e `5xx` ao consultar uma fonte.

2.5. QUANDO nenhuma fonte entregar dado elegível, O SISTEMA DEVE registrar a execução como `failed` ou `no_new_data`, encerrar com código coerente e manter a última execução bem-sucedida intacta.

2.6. O SISTEMA DEVE concluir uma execução em menos de quatro minutos, para reduzir sobreposição com o próximo disparo.

### Requisito 3 — Persistência aditiva no RDS existente

**História de usuário:** Como mantenedor, quero preservar medições e resultados no PostgreSQL atual, para obter histórico sem criar outro banco.

#### Critérios de aceitação

3.1. O SISTEMA DEVE introduzir os modelos e índices do Nautam Live por migração Prisma exclusivamente aditiva.

3.2. A migração NÃO DEVE remover, renomear, tornar obrigatório ou mudar o tipo de tabela, coluna, índice ou restrição existente.

3.3. O SISTEMA DEVE armazenar separadamente observações de origem, configuração reprodutível da simulação, picos decodificados, métricas e linha de base MQTT.

3.4. O SISTEMA DEVE impedir duplicação de uma observação pela combinação de provedor, identificador do sensor ou série, parâmetro e instante observado.

3.5. A tarefa DEVE obter `DATABASE_URL` do Secrets Manager pelo papel de execução existente; a URL e a senha NÃO DEVEM aparecer em código, workflow ou logs.

3.6. O Painel_Publico DEVE oferecer ao menos 30 dias de série histórica enquanto houver dados armazenados, sem exigir um banco adicional.

### Requisito 4 — Transmissão e decodificação pelo Nautam

**História de usuário:** Como visitante técnico, quero ver valores reais atravessarem o algoritmo Nautam, para verificar o comportamento da multiplexação harmônica em condições reproduzíveis.

#### Critérios de aceitação

4.1. QUANDO houver observações elegíveis, O SISTEMA DEVE selecionar no máximo 12 valores e atribuir cada um de forma determinística a um canal HPM 1.0 distinto.

4.2. O SISTEMA DEVE usar `HPM10_F0 = 16.384 Hz`, `channelTable`, `compositeSignal` e `decodeFft` do núcleo TypeScript existente, sem criar uma segunda implementação do H16.

4.3. O SISTEMA DEVE normalizar cada valor para uma amplitude limitada usando faixa e unidade documentadas por parâmetro, preservando o valor e a unidade originais separadamente.

4.4. O SISTEMA DEVE adicionar ruído branco gaussiano controlado por `snrDb` e por uma semente persistida, de forma que a execução possa ser reproduzida.

4.5. O SISTEMA DEVE preservar `sampleRate`, duração, número de amostras, limiar de detecção, SNR solicitado, SNR medido, semente, canais esperados e picos decodificados.

4.6. O SISTEMA DEVE respeitar os limites existentes de amostras e a validação de Nyquist da API.

### Requisito 5 — Métricas honestas e reproduzíveis

**História de usuário:** Como avaliador independente, quero métricas definidas e limitações explícitas, para não confundir simulação de software com desempenho de rádio real.

#### Critérios de aceitação

5.1. O SISTEMA DEVE calcular por execução: canais esperados, verdadeiros positivos, falsos positivos, falsos negativos, precisão, taxa de acerto/recall, erro absoluto médio do valor normalizado e tempo de processamento.

5.2. O SISTEMA DEVE comparar canais por razão H16 esperada e tolerância de frequência documentada, em vez de aceitar qualquer pico próximo sem limite.

5.3. O SISTEMA DEVE executar uma matriz reprodutível de SNRs para estimar a menor SNR testada que mantenha taxa de acerto de pelo menos 95% e precisão de pelo menos 99%; se nenhuma satisfizer, DEVE informar “não atingida”.

5.4. O SISTEMA DEVE medir separadamente o efeito dos pares de canais HPM 1.0 mais próximos em frequência, reportando separação em hertz, separação em bins FFT e taxa de acerto do par.

5.5. O SISTEMA DEVE chamar de capacidade apenas o número de valores por quadro simulado, duração do quadro e taxa lógica derivada; NÃO DEVE declarar capacidade de canal de rádio, BER física, alcance ou eficiência energética.

5.6. O SISTEMA DEVE rotular resultados provenientes de ruído gerado em software como “simulados”.

### Requisito 6 — Linha de base MQTT comparável

**História de usuário:** Como visitante técnico, quero comparar o Nautam a uma referência MQTT explícita, para entender o custo de enquadramento sem conclusões indevidas.

#### Critérios de aceitação

6.1. O SISTEMA DEVE serializar a mesma carga lógica das observações em representação canônica e calcular o tamanho de uma publicação MQTT 3.1.1 para QoS 0 e QoS 1.

6.2. O cálculo DEVE incluir byte de controle, campo Remaining Length, comprimento e bytes UTF-8 do tópico, identificador de pacote quando aplicável e payload.

6.3. O cálculo DEVE mostrar separadamente payload, overhead MQTT e total MQTT, além do tamanho do vetor de amostras do Nautam se serializado como `Float64`.

6.4. O painel DEVE informar que o cálculo MQTT exclui CONNECT/CONNACK amortizados, TCP, IP, TLS, Ethernet/rádio, retransmissões, energia e comportamento do broker.

6.5. O SISTEMA NÃO DEVE apresentar a diferença de bytes entre o sinal simulado e MQTT como prova de superioridade de um protocolo no mundo físico.

### Requisito 7 — Painel público e atribuição

**História de usuário:** Como visitante, quero acompanhar a demonstração e sua proveniência, para verificar o dado real e interpretar corretamente o experimento.

#### Critérios de aceitação

7.1. O SISTEMA DEVE publicar o Painel_Publico em uma URL HTTPS sob o serviço Fastify existente, sem um segundo serviço ECS sempre ativo.

7.2. O painel DEVE mostrar a última execução, estado da fonte, idade do dado original, valores e unidades, canal/razão H16, SNR, taxa de acerto, precisão, erro de amplitude, tempo de processamento e linha de base MQTT.

7.3. O painel DEVE mostrar série histórica selecionável de pelo menos 24 horas, 7 dias e 30 dias, quando os dados existirem.

7.4. O painel DEVE exibir nome da fonte, provedor original, licença, link da licença, URL de origem e instante da observação.

7.5. O painel DEVE exibir, sem ocultação: **“simulação de sinal com dados reais; energia e interferência em campo não medidas”**.

7.6. ENQUANTO a última execução bem-sucedida tiver mais de 15 minutos, O painel DEVE marcar os dados como desatualizados.

7.7. Rotas administrativas e dados brutos DEVERÃO continuar protegidos por chave de API e escopo; somente a página e um resumo estritamente necessário ao Painel_Publico poderão ser abertos.

7.8. O endpoint público do painel DEVE limitar período, paginação e quantidade de pontos retornados para proteger o RDS e a tarefa da API.

### Requisito 8 — Segurança, privacidade e operação lean

**História de usuário:** Como founder solo, quero risco e custo limitados, para operar o MVP sem construir uma plataforma prematura.

#### Critérios de aceitação

8.1. A tarefa agendada DEVE usar a imagem já publicada no ECR, o cluster, as sub-redes e o acesso ao RDS existentes.

8.2. A tarefa agendada NÃO DEVE aceitar conexões de entrada e DEVE usar papel IAM mínimo para logs, leitura dos segredos estritamente necessários e execução no ECS.

8.3. A chave da OpenAQ DEVE ficar no Secrets Manager e NÃO DEVE aparecer no banco, painel ou logs.

8.4. O SISTEMA NÃO DEVE ingerir ou publicar nome de contribuidor, e-mail, contato, endereço residencial, identificador de conta, trajetória, imagem ou identificador de dispositivo de pessoa física.

8.5. O painel NÃO DEVE publicar coordenadas exatas de sensores comunitários ou móveis; para o MVP, somente estações institucionais fixas são elegíveis.

8.6. O SISTEMA DEVE registrar erros sem incluir segredos, corpo completo de respostas externas ou dados não selecionados.

8.7. O custo incremental mensal DEVE permanecer abaixo de US$ 10, sem NAT Gateway, novo ALB, novo RDS ou segundo serviço Fargate permanente.

8.8. O cálculo de custo DEVE considerar pelo menos 8.760 tarefas mensais, cobrança mínima de um minuto por tarefa Fargate, IPv4 público durante a execução, um segredo adicional, logs e crescimento do RDS.

### Requisito 9 — Fora de escopo

**História de usuário:** Como responsável pelo roadmap, quero fronteiras explícitas, para concluir a prova antes de investir em hardware ou plataforma.

#### Critérios de aceitação

9.1. Hardware e rádio reais, medição de energia, propagação física, certificação de espectro e ensaios de campo DEVEM permanecer fora do MVP.

9.2. OSINT de dispositivos, varredura Wi-Fi, descoberta de redes e coleta de identificadores de terceiros DEVEM permanecer fora do MVP.

9.3. Multiusuário, contas de cliente, cobrança, multiambiente, multiconta, AWS IoT Core e observabilidade avançada DEVEM permanecer fora do MVP.

9.4. O MVP NÃO DEVE introduzir broker MQTT; a comparação MQTT será exclusivamente analítica.

9.5. O MVP NÃO DEVE criar uma plataforma genérica de conectores; somente os adaptadores da Fonte_Inicial e da Fonte_Reserva serão especificados.
### Requisito 10 — Padrão editorial e teses de uso do painel

**História de usuário:** Como Guilherme (decisão de 03/11/2026), quero que o painel siga o dogma editorial da Hubstry e explique o que cada dado significa e para quem serve, para que gestores públicos, investidores, executivos (C-level), pesquisadores e cidadãos entendam o valor sem precisar de conhecimento técnico prévio.

#### Critérios de aceitação

10.1. O painel DEVE seguir o dogma editorial da Hubstry: toda sigla escrita por extenso entre parênteses na primeira ocorrência (sigla estrangeira com o original e a tradução em português); contexto mínimo para termos técnicos, jargões e marcas pouco conhecidas, em frases curtas, com no máximo uma explicação por frase.

10.2. O tom DEVE ser de consultoria: analítico e teórico-expositivo, nunca hermético, sem sacrificar a legibilidade.

10.3. Para cada família de dados (qualidade do ar; energia elétrica), o painel DEVE apresentar, em acordeões recolhíveis, uma tese curta com: (a) o que o dado mede, em linguagem simples; (b) o que ele significa; (c) como pode ser usado.

10.4. O uso DEVE ser descrito por ator da hélice quíntupla de inovação (Carayannis e Campbell): Estado e decisores governamentais; setor privado, investidores e C-level de empresas; sociedade civil e cidadãos; academia e ciência; e meio ambiente, como quinta hélice que atravessa as demais.

10.5. O painel DEVE apresentar, em acordeão próprio, a tese de OSINT (Open Source Intelligence, inteligência de fontes abertas) do Nautam Live: inteligência produzida exclusivamente a partir de dados abertos publicados por suas fontes para reutilização, com proveniência e licença verificáveis. A tese DEVE explicitar a fronteira ética e jurídica: nada de varredura de dispositivos ou redes, coleta de identificadores de terceiros ou dado pessoal (LGPD, Lei Geral de Proteção de Dados Pessoais), em coerência com o Requisito 9.2.

10.6. As teses NÃO DEVEM atribuir ao Nautam resultados não medidos: valem as mesmas restrições do Requisito 5 e a declaração do Requisito 7.5.

10.7. ONDE houver afirmação factual sobre a fonte ou o fenômeno, o painel DEVE citar a fonte com link.

### Requisito 11 — Próximas fontes (backlog, fora do MVP)

**História de usuário:** Como responsável pelo roadmap, quero registrar as fontes pesquisadas pela Luna em 03/11/2026, para ampliar o Nautam Live depois da E3 sem reabrir o escopo agora.

#### Critérios de aceitação

11.1. As próximas fontes candidatas, em ordem: CEMADEN (Centro Nacional de Monitoramento e Alertas de Desastres Naturais, pluviômetros); PNBOIA (Programa Nacional de Boias, Marinha do Brasil); SPTrans Olho Vivo (posição de ônibus em São Paulo). Em seguida: Rede SONDA (Sistema de Organização Nacional de Dados Ambientais, INPE; CC BY 4.0), ANA HidroWeb (Agência Nacional de Águas e Saneamento Básico), Agritempo, INPE Queimadas, Banco Central e ANP (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis). Alerta Rio em trilha paralela de confirmação de acesso.

11.2. Nenhuma fonte do backlog DEVE ser integrada antes de confirmar endpoint, autenticação, cota e licença de redistribuição, pelo mesmo critério fail-closed do Requisito 1.

11.3. Cada nova fonte DEVE entrar por um adaptador pequeno no contrato `LiveSourceAdapter`, sem criar plataforma genérica de conectores (Requisito 9.5).

11.4. O painel DEVE distinguir leituras de sensores físicos de indicadores estatísticos (por exemplo, Banco Central, ANP, ANTAQ), que não demonstram o mesmo tipo de capacidade.
