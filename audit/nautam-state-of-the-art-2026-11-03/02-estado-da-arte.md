# Estado da arte e posição tecnológica do Nautam

**Corte:** 03/11/2026
**Escopo:** técnicas próximas ao mecanismo realmente implementado, não revisão genérica de IoT.
**Limite:** não constitui busca patentária de anterioridade ou liberdade de operação.

## 1. Classificação técnica do sinal

O sinal implementado é:

\[
s(t)=\sum_{k=1}^{K}A_k\sin(2\pi r_k f_0t+\phi_k),\quad K\le 12,\quad r_k=a_k/b_k.
\]

O Nautam Live usa frequências fixas, fase zero e amplitudes contínuas derivadas das leituras. A classificação mais precisa é:

- **FDM/multisine esparso e não uniforme**, porque vários tons coexistem em frequências distintas;
- **modulação vetorial de amplitude multicarrier**, quando cada amplitude representa diretamente um valor;
- **ASK multicarrier**, caso amplitudes sejam quantizadas em símbolos;
- **não FSK**, pois FSK representa símbolos pela escolha/deslocamento de frequência;
- **não OFDM na configuração atual**, pois nem todos os tons são ortogonais na janela usada e não existe framing, preâmbulo, prefixo cíclico ou equalização.

O termo “harmônico de f0” também precisa de precisão. `2f0` e `3f0` são harmônicos inteiros de f0; `4f0/3`, `7f0/5` e `f0` não pertencem todos à mesma série harmônica de f0. Com denominador comum 60, todos os tons HPM podem ser escritos como múltiplos inteiros de `f0/60`. Portanto, são uma seleção esparsa de subportadoras de uma grade uniforme com fundamental comum `f0/60`.

## 2. Precedentes científicos diretamente relevantes

### 2.1 FDM e OFDM

FDM por subportadoras é anterior ao Nautam por décadas. O padrão de telemetria [IRIG 106-24R1, capítulo 3](https://www.irig106.org/docs/106-24R1/chapter3.pdf) ainda especifica canais de telemetria FDM por subportadoras, incluindo largura de banda e referências de compensação.

A transmissão multicanal ortogonal foi formalizada por R. W. Chang em 1966, com condições para evitar interferência entre canais em meio linear de banda limitada: “Synthesis of Band-Limited Orthogonal Signals for Multichannel Data Transmission”, [DOI 10.1002/j.1538-7305.1966.tb02435.x](https://doi.org/10.1002/j.1538-7305.1966.tb02435.x). Weinstein e Ebert implementaram modulação/demodulação FDM por DFT em 1971: “Data Transmission by Frequency Division Multiplexing Using the Discrete Fourier Transform”, [DOI 10.1109/TCOM.1971.1090705](https://doi.org/10.1109/TCOM.1971.1090705).

Em OFDM/DMT, coeficientes complexos já transportam amplitude e fase em várias subportadoras. Portanto, “codificar informação em amplitudes de tons e recuperar por FFT” não é contribuição matemática nova isoladamente.

### 2.2 Estimação multitom

Rife e Boorstyn analisaram estimação de frequência, amplitude e fase de tons em amostras finitas e ruidosas, incluindo limites de Cramér–Rao e máxima verossimilhança:

- “Single Tone Parameter Estimation from Discrete-Time Observations”, [DOI 10.1109/TIT.1974.1055282](https://doi.org/10.1109/TIT.1974.1055282), 1974;
- “Multiple Tone Parameter Estimation from Discrete-Time Observations”, [DOI 10.1002/j.1538-7305.1976.tb02941.x](https://doi.org/10.1002/j.1538-7305.1976.tb02941.x), 1976.

O uso de janela e os compromissos entre largura de lóbulo principal, sidelobes, scalloping e largura equivalente de ruído são sistematizados por Harris: “On the Use of Windows for Harmonic Analysis with the DFT”, [DOI 10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837), 1978. Análises multitom modernas confirmam que janelas calibradas permitem estimar amplitude, frequência e fase, em vez de apenas localizar o maior bin. [Gade e Herlufsen, JASA 116](https://pubmed.ncbi.nlm.nih.gov/15295999/)

O receptor atual do Nautam, que lê um bin conhecido ou detecta máximos locais sem interpolação, é uma solução simples diante desse estado da arte.

### 2.3 Sincronização

Sistemas multicarrier reais precisam estimar timing, carrier-frequency offset (CFO), sampling-frequency offset (SFO) e canal. Dois marcos:

- Moose, “A Technique for Orthogonal Frequency Division Multiplexing Frequency Offset Correction”, [DOI 10.1109/26.328961](https://doi.org/10.1109/26.328961), 1994;
- Schmidl e Cox, “Robust Frequency and Timing Synchronization for OFDM”, [DOI 10.1109/26.650240](https://doi.org/10.1109/26.650240), 1997.

A racionalidade da grade pode fornecer um período comum, mas não substitui aquisição de quadro ou estimação. CFO desloca todas as portadoras; SFO escala a grade; phase noise e Doppler espalham energia; multipercurso altera a amplitude de cada tom.

### 2.4 DTMF e detecção seletiva

DTMF usa pares de tons e detecção seletiva. [ITU-T Q.23](https://www.itu.int/rec/T-REC-Q.23) é um precedente importante porque demonstra que detecção por múltiplas frequências é madura. Também mostra que relações harmônicas, distorção e “twist” precisam ser controlados; uma assinatura de tons não é automaticamente autenticação.

### 2.5 Analog joint source–channel coding

Mapear diretamente valores contínuos de sensores em parâmetros de um sinal se aproxima de **analog joint source–channel coding**, onde a qualidade degrada gradualmente em vez de produzir necessariamente um bit errado. Essa literatura torna MAE/NMSE/outage mais adequados que BER enquanto o Nautam não definir símbolos binários. Um exemplo de arquitetura para sensores é [arXiv:2004.01004](https://arxiv.org/abs/2004.01004).

## 3. Condições que separam modelo ideal de enlace real

| Aspecto | Modelo Nautam atual | Exigência no estado da arte |
|---|---|---|
| Início do quadro | Índice zero conhecido | Preamble, correlação e estimação de timing. |
| Frequência | `f0` exato e comum | Estimação/correção de CFO e SFO. |
| Fase | Transmissão em fase zero | Rastreamento de fase ou receptor não coerente analisado. |
| Canal | Ganho implícito unitário | Pilotos, estimação de `H(fk)` e equalização. |
| Ruído | AWGN branco sintético | AWGN, ruído colorido/impulsivo, interferidores, fading e multipercurso. |
| Não linearidade | Soma perfeita em float64 | DAC/ADC, PA/LNA, AGC, clipping, quantização e intermodulação. |
| Detecção | Um bin por canal + limiar | Janela, banco de filtros, Goertzel, NUDFT, interpolação ou ajuste conjunto. |
| Integridade | Nenhuma no sinal | CRC/MAC criptográfico, framing e anti-replay. |
| Confiabilidade | Sem FEC/ARQ | FEC, interleaving, confirmação/retransmissão conforme requisito. |
| Acesso múltiplo | 12 amplitudes num quadro | MAC, colisão, potência near-far e coordenação. |

### Intermodulação e PAPR

A soma de 12 tons pode ter alto crest factor/PAPR. Um front-end não linear gera somas e diferenças que podem coincidir com outros canais. Na grade HPM expressa em índices de `f0/60`, há relações como `60+90=150`, `80+100=180` e `84+96=180`. Produtos de intermodulação podem criar falsos canais mesmo quando os tons originais são bem separados.

Antes de qualquer alegação de robustez física, devem ser medidos PAPR, compressão, SFDR, EVM/NMSE e produtos de intermodulação.

## 4. Comparação com tecnologias existentes

A tabela não iguala camadas diferentes. MQTT e CoAP são protocolos de aplicação; as demais tecnologias incluem PHY/MAC ou rede completa.

| Tecnologia | Princípio e multiplexação | Sincronização/robustez | Capacidade e consumo | Complexidade/hardware | Segurança e maturidade | Relação correta com Nautam |
|---|---|---|---|---|---|---|
| **FDM clássico / telemetria IRIG** | Uma subportadora por canal, com bandas definidas. | Separação por filtros; padrões tratam flutter e referência. | Depende da modulação e largura de cada canal. | Rádio/gravador e filtros específicos. | Técnica madura e padronizada. | Precedente mais direto para “uma variável por tom”. |
| **OFDM/DMT** | Subportadoras ortogonais em uma janela; QAM/PSK por portadora; FFT/IFFT. | Preamble, pilotos, CFO/SFO, CP, equalização, FEC. Sensível a offset/PAPR. | Alta eficiência espectral demonstrada em padrões reais; energia depende da implementação. | DSP e front-end linear; amplo suporte em silício. | Muito madura em Wi-Fi, LTE, DSL e broadcast. | Nautam é um multitone simplificado; não herda garantias OFDM sem seus mecanismos. |
| **MFSK/GFSK** | Símbolo escolhe frequência; BLE usa GFSK. | Pode ser não coerente; hopping combate interferência/fading no BLE. | Taxa e sensibilidade dependem do espaçamento/tempo de símbolo. | Implementação RF madura e simples. | BLE possui pilha, interoperabilidade e segurança completas. | Nautam não é FSK, pois varia amplitude em tons fixos. |
| **IEEE 802.15.4** | Família PHY/MAC de baixa taxa; inclui modulações e SUN PHYs. [IEEE/ISO/IEC 8802-15-4-2024](https://standards.ieee.org/ieee/8802-15-4/11701) | Preamble, acesso ao meio, framing e mecanismos definidos pelo padrão. | Perfis e taxas especificados; energia medida por implementação. | Chips certificados e interoperáveis. | Padrão industrial maduro. | Referência de requisitos mínimos para transformar uma forma de onda em protocolo IoT. |
| **Bluetooth LE 6.3** | GFSK em 2,4 GHz, frequency hopping, LE 1M/2M/Coded. [PHY oficial](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core_v6.3/out/en/low-energy-controller/radio-physical-layer-specification.html) | Preamble, access address, sincronização e hopping definidos. | Taxas e potência especificadas/testáveis. | Silício commodity e certificação. | Pilha completa, CCM e LE Secure Connections. | Comparar energia exige mesmo hardware, payload, segurança e confiabilidade. |
| **LoRa/LoRaWAN** | LoRa PHY usa chirp spread spectrum; LoRaWAN define link/MAC. [TS001-1.0.4](https://resources.lora-alliance.org/technical-specifications/ts001-1-0-4-lorawan-l2-1-0-4-specification) | Preamble, dechirp/FFT, correções e spreading factors; CFO/SFO continuam relevantes. [Ghanaatian et al.](https://arxiv.org/abs/1811.04146) | Longo alcance/baixa taxa, com trade-offs por SF; energia depende do airtime. | Transceptor LoRa e gateway. | Ecossistema e certificação maduros. | O uso de FFT no receptor não torna a forma de onda equivalente ao Nautam. |
| **Wi‑Fi HaLow / 802.11ah** | OFDM sub-1 GHz e MAC Wi-Fi; consolidado em [IEEE 802.11-2024](https://standards.ieee.org/ieee/802.11/10548/). | Mecanismos Wi-Fi, canais, coding e Restricted Access Window. | Meta de pelo menos 100 kb/s no amendment e alcance de até 1 km sob condições do padrão. [IEEE](https://standards.ieee.org/ieee/8802-11_2018_Amd_2/10081) | Chipset e AP compatíveis. | Produto/padrão maduro. | Comparador multicarrier IoT mais próximo, mas muito mais completo. |
| **NB‑IoT / LTE‑M** | 3GPP celular; NB-IoT introduzido com eMTC no Release 13. [3GPP](https://www.3gpp.org/images/presentations/3GPP_Standards_for_IoT.pdf) | Sincronização, canal, coding, HARQ, acesso e rede operadora. | Taxa/cobertura/energia dependem de configuração e rede. | Modem certificado e espectro licenciado. | Pilha comercial madura; PHY no [TS 36.211 Rel-19](https://www.etsi.org/deliver/etsi_ts/136200_136299/136211/19.03.00_60/ts_136211v190300p.pdf). | Não é substituível por uma tabela de tons sem nova rede e certificação. |
| **MQTT** | Publish/subscribe cliente–broker, normalmente sobre TCP/TLS. [MQTT 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html) | Confiabilidade/QoS na aplicação e transporte. | Bytes dependem de tópico, propriedades, sessão, TLS e rede. | Broker e clientes; independente do PHY. | Padrão OASIS maduro. | Só pode ser baseline de mensagem/aplicação, não concorrente físico direto. |
| **CoAP** | REST para nós e redes restritos, originalmente sobre UDP. [RFC 7252](https://www.rfc-editor.org/rfc/rfc7252.html) | Confirmable messages, congestion control simples; DTLS/OSCORE conforme perfil. | Menor overhead em alguns cenários, não universal. | Pilha IP restrita. | Padrão IETF maduro. | Também camada de aplicação; comparação energética precisa fixar bearer. |

Um estudo no mesmo sistema NB-IoT encontrou diferenças condicionadas entre CoAP/UDP e MQTT/TCP, reforçando que a comparação depende da pilha completa: “Impact of CoAP and MQTT on NB-IoT System Performance”, [DOI 10.3390/s19010007](https://doi.org/10.3390/s19010007).

## 5. Segurança de camada física

O estado da arte em physical-layer security (PLS) inclui wiretap/secrecy coding, geração de chaves pela reciprocidade do canal, artificial noise, beamforming, autenticação por CSI/RF fingerprint e detecção de spoofing. Uma revisão focada em IoT é “Physical Layer Security for Authentication, Confidentiality, and Malicious Node Detection”, [DOI 10.1109/COMST.2023.3327327](https://doi.org/10.1109/COMST.2023.3327327).

Para que “assinatura timbral” fosse autenticação física, seria necessário demonstrar:

- característica originada no hardware, não um padrão copiável por software;
- estabilidade entre temperatura, tempo, distância e receptores;
- separação da resposta do transmissor e do canal;
- FAR, FRR, ROC/EER e ataques com SDR;
- resistência a replay, synthesis, relay e emulação;
- combinação com autenticação criptográfica e anti-replay.

O HSL atual não atende a esses critérios e não usa observação física. PLS pode complementar criptografia, não justificar sua ausência. O HMAC possui construção padronizada específica; concatenar segredo com hash não é equivalente a alegar HMAC sem análise. [FIPS 198-1](https://csrc.nist.gov/csrc/media/publications/fips/198/1/final/documents/fips-198-1_final.pdf)

## 6. Originalidade

| Categoria | Avaliação | Fundamentação |
|---|---|---|
| Inovação matemática | **Não demonstrada** | Frações coprimas, MMC, FDM e ortogonalidade em janela são conhecidos. A grade racional HPM equivale a subportadoras inteiras sobre `f0/60`. |
| Inovação algorítmica | **Baixa / não demonstrada** | Síntese senoidal, FFT, pico local, AWGN e normalização são técnicas padrão. Não há detector novo comparado a estimadores existentes. |
| Inovação de arquitetura | **Possível** | Combinação de tabela HPM, mapeamento de sensores, HALE e pipeline Live é uma organização específica. A vantagem dessa organização ainda não foi medida. |
| Inovação de protocolo | **Não demonstrada** | Não existe especificação executável de PHY/MAC, framing, sincronização, confiabilidade ou interoperabilidade. |
| Inovação de implementação | **Confirmada em grau modesto** | Há porte TS próprio, integração Fastify/Prisma/AWS e painel reproduzível. |
| Aplicação experimental | **Confirmada** | Dados externos alimentam uma simulação multitone e métricas públicas. |
| Novidade científica | **Não verificada** | Não houve busca completa em IEEE/ACM/Espacenet/WIPO/USPTO/INPI nem comparação de reivindicações. |

A contribuição sustentável mais próxima hoje é **uma bancada aberta para experimentar representação multitone de vetores de sensores**, não um novo padrão de comunicação comprovado.

## 7. Comparação de desempenho que seria válida

Uma comparação futura deve manter constantes:

- banda ocupada e máscara espectral;
- potência média/EIRP e antena;
- distância e canal;
- hardware, taxa de amostragem e clock;
- número de valores, resolução de quantização e período de atualização;
- framing, CRC, FEC, retransmissões e probabilidade de entrega;
- autenticação/confidencialidade;
- tempo no ar;
- energia de TX, RX, aquisição e DSP.

Métricas adequadas:

- se amplitude contínua: MAE/NMSE, outage e distorção por canal;
- se símbolos discretos: SER/BER e PER;
- em ambos: recall/precisão de presença, falso pico/quadro, goodput, latência, energia por leitura entregue, PAPR, EVM, CFO/SFO tolerados e intervalo de confiança.

O baseline MQTT atual é apenas uma contagem de bytes de aplicação. Ele não mede energia nem eficiência do Nautam, pois compara JSON com um vetor float64 de sinal e exclui PHY, transporte, TLS, retransmissão e broker.

## 8. Referências essenciais

1. Chang, R. W. (1966). Synthesis of Band-Limited Orthogonal Signals for Multichannel Data Transmission. [DOI](https://doi.org/10.1002/j.1538-7305.1966.tb02435.x).
2. Weinstein, S. B.; Ebert, P. M. (1971). Data Transmission by Frequency Division Multiplexing Using the DFT. [DOI](https://doi.org/10.1109/TCOM.1971.1090705).
3. Rife, D.; Boorstyn, R. (1974). Single Tone Parameter Estimation. [DOI](https://doi.org/10.1109/TIT.1974.1055282).
4. Rife, D.; Boorstyn, R. (1976). Multiple Tone Parameter Estimation. [DOI](https://doi.org/10.1002/j.1538-7305.1976.tb02941.x).
5. Harris, F. J. (1978). Windows for Harmonic Analysis with the DFT. [DOI](https://doi.org/10.1109/PROC.1978.10837).
6. Moose, P. H. (1994). OFDM Frequency Offset Correction. [DOI](https://doi.org/10.1109/26.328961).
7. Schmidl, T.; Cox, D. (1997). Robust Frequency and Timing Synchronization for OFDM. [DOI](https://doi.org/10.1109/26.650240).
8. [IRIG 106-24R1, Chapter 3](https://www.irig106.org/docs/106-24R1/chapter3.pdf), Frequency Division Multiplexing Telemetry Standards, 2025.
9. [IEEE/ISO/IEC 8802-15-4-2024](https://standards.ieee.org/ieee/8802-15-4/11701).
10. [IEEE 802.11-2024](https://standards.ieee.org/ieee/802.11/10548/).
11. [Bluetooth Core 6.3 PHY](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core_v6.3/out/en/low-energy-controller/radio-physical-layer-specification.html), 2026.
12. [LoRaWAN L2 1.0.4](https://resources.lora-alliance.org/technical-specifications/ts001-1-0-4-lorawan-l2-1-0-4-specification).
13. [3GPP/ETSI TS 36.211 v19.3.0](https://www.etsi.org/deliver/etsi_ts/136200_136299/136211/19.03.00_60/ts_136211v190300p.pdf).
14. [MQTT 5.0 OASIS](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html).
15. [CoAP RFC 7252](https://www.rfc-editor.org/rfc/rfc7252.html).

Conteúdo das fontes foi resumido e reformulado para conformidade com restrições de licenciamento.