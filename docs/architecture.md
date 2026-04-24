# 4-Layer Protocol Architecture

## [PT-BR] Arquitetura em 4 Camadas | [EN] 4-Layer Protocol Architecture

---

## Visao Geral / Overview

O protocolo IoT Hubstry e organizado em 4 camadas distintas, cada uma com
responsabilidades bem definidas. A base matematica e fornecida pelo
framework HPG 1.0, que define o espaco de canais harmonicos racionais.

The IoT Hubstry protocol is organized in 4 distinct layers, each with
well-defined responsibilities. The mathematical foundation is provided
by the HPG 1.0 framework, which defines the rational harmonic channel space.

```
+----------------------------------------------------------+
|                   LAYER 4: SECURITY                       |
|  H-Challenge/Response | Intrusion Detection | Key Rotation|
+----------------------------------------------------------+
|                   LAYER 3: ADDRESSING (HALE)              |
|  Pipeline: f0 -> H -> h -> psi -> c -> M -> g            |
+----------------------------------------------------------+
|                   LAYER 2: SIGNAL (HPG)                   |
|  Composite Signal s(t) | FFT Decode | Spectral Verify     |
+----------------------------------------------------------+
|                   LAYER 1: GRID (HPG)                     |
|  H_N | O_N | Euler Totient | HPM 1.0 Config              |
+----------------------------------------------------------+
```

---

## Layer 1: Harmonic Grid (HPG)

### PT-BR

A camada de grade define o espaco de enderecos fundamentais para o protocolo.
E baseada no conjunto harmonico racional H_N e na Omnigrid O_N.

**Conceitos:**
- H_N = {a/b em Q+ : gcd(a,b)=1, b<=N, a<=N}
- |H_N| = sum(phi(b)) para b=1 ate N, onde phi e a funcao totiente de Euler
- O_N = H_N x {-1, +1}, |O_N| = 2 * |H_N|
- Para N=16: |H_16| = 80 canais, |O_16| = 160 enderecos

**Modulo:** `hpg_core/omnigrid.py`, `hpg_core/hpm_config.py`

**Responsabilidades:**
1. Construir H_N via funcao totiente de Euler
2. Expandir para Omnigrid 2D O_N
3. Definir a tabela de canais HPM 1.0 (12 canais praticos)
4. Calcular prioridade de canal: P(a/b) = 1/(a+b)
5. Calcular periodo de ressincronizacao: T_sync = lcm(b1,...,bn)/f0

### EN

The grid layer defines the fundamental address space for the protocol.
It is based on the Rational Harmonic Subdivision Set H_N and the Omnigrid O_N.

**Concepts:**
- H_N = {a/b in Q+ : gcd(a,b)=1, b<=N, a<=N}
- |H_N| = sum(phi(b)) for b=1 to N, where phi is Euler totient
- O_N = H_N x {-1, +1}, |O_N| = 2 * |H_N|
- For N=16: |H_16| = 80 channels, |O_16| = 160 addresses

**Module:** `hpg_core/omnigrid.py`, `hpg_core/hpm_config.py`

**Responsibilities:**
1. Build H_N via Euler totient function
2. Expand to 2D Omnigrid O_N
3. Define HPM 1.0 channel table (12 practical channels)
4. Calculate channel priority: P(a/b) = 1/(a+b)
5. Calculate resynchronization period: T_sync = lcm(b1,...,bn)/f0

---

## Layer 2: Signal Processing (HPG)

### PT-BR

A camada de sinal gerencia a composicao e decomposicao de sinais harmonicos
sobre a grade definida na Camada 1.

**Sinal Composto:**
    s(t) = sum A_k * sin(2*pi*(a_k/b_k)*f0*t + phi_k)

**Operacoes:**
1. Gerar sinal composto a partir de canais ativos
2. Decodificar sinal recebido via FFT
3. Extrair frequencia, amplitude e fase de cada componente
4. Verificar integridade espectral das razoes racionais

**Modulo:** `hpg_core/signal_processing.py`, `hpg_core/spectral_verification.py`

### EN

The signal layer manages composition and decomposition of harmonic signals
over the grid defined in Layer 1.

**Composite Signal:**
    s(t) = sum A_k * sin(2*pi*(a_k/b_k)*f0*t + phi_k)

**Operations:**
1. Generate composite signal from active channels
2. Decode received signal via FFT
3. Extract frequency, amplitude, and phase of each component
4. Verify spectral integrity of rational ratios

**Module:** `hpg_core/signal_processing.py`, `hpg_core/spectral_verification.py`

---

## Layer 3: Addressing (HALE)

### PT-BR

A camada de enderecamento implementa o pipeline HALE para mapear
dispositivos e canais na grade harmonica.

**Pipeline HALE:**
    f0 -> H (quantizacao) -> h (vetor harmonico) -> psi (enderecamento)
    -> c (vetor de canais) -> M (lookup) -> g (saida)

**Funcoes PSI (enderecamento):**
- psi1: Indice direto (mapeamento identidade)
- psi2: Ativacao binaria (baseada em paridade do denominador)
- psi3: Fatoracao prima (baseada em fatores primos de b)
- psi4: Ponderado/aprendido (heuristica de pontuacao)

**Nota sobre Paper 1:**
O pipeline HALE e conceitualmente referenciado do paper
DOI: 10.5281/zenodo.18901934 (CC BY-NC-ND 4.0) como motivacao
teorica. A implementacao e independente e baseada no HPG 1.0
(DOI: 10.5281/zenodo.19056387, CC BY 4.0).

**Modulo:** `hale_core/hale_equation.py`, `hale_core/psi_functions.py`

### EN

The addressing layer implements the HALE pipeline for mapping devices
and channels on the harmonic grid.

**HALE Pipeline:**
    f0 -> H (quantization) -> h (harmonic vector) -> psi (addressing)
    -> c (channel vector) -> M (lookup) -> g (output)

**PSI Functions (addressing):**
- psi1: Direct index (identity mapping)
- psi2: Binary activation (based on denominator parity)
- psi3: Prime factorization (based on prime factors of b)
- psi4: Weighted/learned (heuristic scoring)

**Note on Paper 1:**
The HALE pipeline is conceptually referenced from Paper
DOI: 10.5281/zenodo.18901934 (CC BY-NC-ND 4.0) as theoretical
motivation. The implementation is independent and based on HPG 1.0
(DOI: 10.5281/zenodo.19056387, CC BY 4.0).

**Module:** `hale_core/hale_equation.py`, `hale_core/psi_functions.py`

---

## Layer 4: Security

### PT-BR

A camada de seguranca fornece autenticacao, deteccao de intrusao e
rotacao de chaves para o protocolo.

**Protocolo H-Challenge/Response (3 etapas):**
1. CHALLENGE: Iniciador seleciona canais harmonicos aleatorios
2. RESPONSE: Responder computa coerencia harmonica com chave compartilhada
3. VERIFY: Iniciador verifica coerencia e deriva chave de sessao

Tamanho estimado do handshake: ~200 bytes (vs TLS 1.3 ~8 KB)

**Deteccao de Intrusao:**
    Delta_phi = |phi_observed - phi_expected| > epsilon

Monitora desvios de fase em cada canal harmonico para detectar
injecao, substituicao ou adulteracao de sinal.

**Rotacao de Chaves (LFSR):**
- Semente derivada de f0 + timestamp
- LFSR Galois com polinomio de feedback configuravel
- Derivacao de chaves via hash do estado + contador

**Modulo:** `security/hsl_auth.py`, `security/intrusion_detection.py`,
           `security/key_rotation.py`

### EN

The security layer provides authentication, intrusion detection, and
key rotation for the protocol.

**H-Challenge/Response Protocol (3 steps):**
1. CHALLENGE: Initiator selects random harmonic channels
2. RESPONSE: Responder computes harmonic coherence with shared key
3. VERIFY: Initiator verifies coherence and derives session key

Estimated handshake size: ~200 bytes (vs TLS 1.3 ~8 KB)

**Intrusion Detection:**
    Delta_phi = |phi_observed - phi_expected| > epsilon

Monitors phase deviations on each harmonic channel to detect
signal injection, substitution, or tampering.

**Key Rotation (LFSR):**
- Seed derived from f0 + timestamp
- Galois LFSR with configurable feedback polynomial
- Key derivation via hash of state + counter

**Module:** `security/hsl_auth.py`, `security/intrusion_detection.py`,
           `security/key_rotation.py`

---

## Data Flow

```
Device A                                    Device B
   |                                           |
   |  [Layer 1] Select channels from H_N       |
   |  [Layer 2] Generate s(t) composite signal |
   |  [Layer 3] Address via psi(h)             |
   |  [Layer 4] H-Challenge ---------->        |
   |                                           |
   |  [Layer 4] <--------- H-Response         |
   |                                           |
   |  [Layer 4] Verify + Session Key ----->    |
   |                                           |
   |  [Layer 2] Exchange data on active channels
   |  [Layer 2] FFT decode received s(t)       |
   |  [Layer 2] Spectral verification          |
   |  [Layer 4] Continuous phase monitoring     |
   |                                           |
```

---

## References

| # | Paper | DOI | License | Usage |
|---|-------|-----|---------|-------|
| 1 | HALE Working Paper v3.0 | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY-NC-ND 4.0 | Theoretical reference |
| 4 | HPG 1.0 Harmonic Protocol Grid | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Implementation base |

---

## Module Dependencies

```
docs/architecture.md (this file)
    |
    +-- hpg_core/omnigrid.py          [Layer 1] (no internal deps)
    +-- hpg_core/hpm_config.py        [Layer 1] (no internal deps)
    +-- hpg_core/signal_processing.py [Layer 2] (numpy for FFT)
    +-- hpg_core/spectral_verification.py [Layer 2] (no internal deps)
    +-- hale_core/hale_equation.py    [Layer 3] (fractions, dataclasses)
    +-- hale_core/psi_functions.py    [Layer 3] (imports hale_equation)
    +-- security/hsl_auth.py          [Layer 4] (hashlib, secrets, time)
    +-- security/intrusion_detection.py [Layer 4] (math, time)
    +-- security/key_rotation.py      [Layer 4] (hashlib, struct, time)
```

---

*Hubstry Deep Tech - 2023-2026*
*CC BY 4.0*