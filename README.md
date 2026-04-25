<div align="center">

# IoT Protocol Hubstry

**HALE + HPG Framework: Harmonic Addressing and Protocol Grid for IoT**

*Framework HALE + HPG: Endereçamento Harmonico e Grade de Protocolo para IoT*

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![HPG 1.0](https://img.shields.io/badge/HPG-1.0-green)](hpg_core/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](hale_core/)

</div>

---
## Incrementos / Latest Implementations

| Módulo | Arquivo | Descrição |
|--------|---------|-----------|
| **HALE Pipeline** | hale_core/hale_equation.py | Pipeline: f0 - H - h - ψ - c - M - g |
| **Funções ψ1-ψ4** | hale_core/psi_functions.py | 4 funções de endereçamento selecionáveis |
| **Omnigrid 2D** | hpg_core/omnigrid.py | Grade O_N = H_N × {-1,+1} com Euler |
| **HPM 1.0** | hpg_core/hpm_config.py | 12 canais harmônicos (f0=16.384 kHz) |
| **Sinal s(t) + FFT** | hpg_core/signal_processing.py | Sinal composto + decodificação FFT |
| **Verificação Espectral** | hpg_core/spectral_verification.py | Integridade de razões racionais |
| **HSL Auth** | security/hsl_auth.py | H-Challenge/Response 3 etapas (~200B) |
| **Detecção de Intrusão** | security/intrusion_detection.py | Desvio de fase Δφ > ε |
| **Rotação LFSR** | security/key_rotation.py | Rotação de chaves via LFSR |


## [PT-BR] Sobre | [EN] About

### Sobre

O **IoT Protocol Hubstry** implementa o framework **HALE + HPG** para comunicação IoT baseada em subdivisões harmônicas racionais. O framework utiliza a **Harmonic Protocol Grid (HPG 1.0)** para definir um espaço de canais baseado em razões racionais a/b onde gcd(a,b)=1, e o pipeline **HALE** (Harmonic Addressing & Labeling Equation) para enderecamento e rotulação de dispositivos.

O conjunto harmônico racional H_N com N=16 produz 80 canais únicos, expandidos para 160 enderecos na Omnigrid O_N = H_N x {-1, +1}. A modularidade espectral natural proporcionada pelas razões harmônicas racionais permite segmentação de redes, autenticação leve e detecção de intrusão por desvio de fase.

**Papers de referencia:**

| Paper | DOI | Licença | Uso |
|-------|-----|---------|-----|
| HALE Working Paper v3.0 | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY-NC-ND 4.0 | Referência teórica (sem derivação de código) |
| HPG 1.0 Harmonic Protocol Grid | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Base para implementação adaptável |

### About

**IoT Protocol Hubstry** implements the **HALE + HPG** framework for IoT communication based on rational harmonic subdivisions. The framework uses the **Harmonic Protocol Grid (HPG 1.0)** to define a channel space based on rational ratios a/b where gcd(a,b)=1, and the **HALE** (Harmonic Addressing & Labeling Equation) pipeline for device addressing and labeling.

The Rational Harmonic Subdivision Set H_N with N=16 yields 80 unique channels, expanded to 160 addresses in the Omnigrid O_N = H_N x {-1, +1}. The natural spectral modularity provided by rational harmonic ratios enables network segmentation, lightweight authentication, and intrusion detection via phase deviation.

**Reference papers:**

| Paper | DOI | License | Usage |
|-------|-----|---------|-------|
| HALE Working Paper v3.0 | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY-NC-ND 4.0 | Theoretical reference (no code derivatives) |
| HPG 1.0 Harmonic Protocol Grid | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Adaptable implementation base |

---

## [PT-BR] Ecossistema Hubstry | [EN] Hubstry Ecosystem

Este repositório faz parte do ecossistema Hubstry:

| Repositório | Descrição | Link |
|-------------|-----------|------|
| **hubstry-security** | Plataforma de cibersegurança com HSL e PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | Framework matematico HALE | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | Protocolo IoT / HPG (este repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Plataforma Qualia Hub | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

This repository is part of the Hubstry ecosystem:

| Repository | Description | Link |
|-----------|-------------|------|
| **hubstry-security** | Cybersecurity platform with HSL and PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | HALE mathematical framework | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | IoT Protocol / HPG (this repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Qualia Hub Platform | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

---

## [PT-BR] Estrutura do Projeto | [EN] Project Structure

```
iot-protocol-hubstry/
|
|-- hale_core/              # HALE pipeline (addressing + labeling)
|   |-- hale_equation.py    # Core pipeline: f0 -> H -> h -> psi -> c -> M -> g
|   |-- psi_functions.py    # 4 addressing functions (psi1-psi4)
|
|-- hpg_core/               # Harmonic Protocol Grid
|   |-- omnigrid.py         # 2D Omnigrid: H_N + Euler totient
|   |-- hpm_config.py       # HPM 1.0 channel table (12 channels)
|   |-- signal_processing.py # Composite signal s(t) + FFT decoding
|   |-- spectral_verification.py # Rational ratio integrity
|
|-- security/               # Security layer
|   |-- hsl_auth.py         # H-Challenge/Response 3-step protocol
|   |-- intrusion_detection.py # Phase deviation detection
|   |-- key_rotation.py     # LFSR key rotation
|
|-- docs/
|   |-- architecture.md     # 4-layer protocol architecture
|
|-- LICENSE                 # CC BY 4.0
|-- README.md               # This file
```

---

## [PT-BR] Conceitos Matemáticos | [EN] Mathematical Concepts

### Conjunto Harmonico Racional / Rational Harmonic Subdivision Set

H_N = {a/b em Q+ : gcd(a,b)=1, b<=N, a<=N}

Cardinalidade: |H_N| = sum(phi(b)) para b=1 ate N

Onde phi(b) e a função totiente de Euler.

Exemplo: |H_16| = 80 canais únicos.

### Omnigrid / Omnigrid

O_N = H_N x {-1, +1}

|O_16| = 80 x 2 = 160 enderecos bidimensionais.

### Sinal Composto / Composite Signal

s(t) = sum A_k * sin(2*pi*(a_k/b_k)*f0*t + phi_k)

### Prioridade de Canal / Channel Priority

P(a/b) = 1/(a+b)

### Periodo de Ressincronização / Resynchronization Period

T_sync = lcm(b1, b2, ...) / f0

---

## [PT-BR] Início Rápido | [EN] Quick Start

### Pré-requisitos / Prerequisites

- Python 3.10+
- numpy (para FFT): `pip install numpy`

### Exemplo / Example

```python
from hpg_core.omnigrid import compute_hn, cardinality_hn, omnigrid_2d
from hpg_core.hpm_config import HPM10Config, get_channel_table
from hpg_core.signal_processing import generate_composite_signal
from hale_core.hale_equation import HALEPipeline

# Compute H_16
h16 = compute_hn(16)
print(f"|H_16| = {cardinality_hn(16)}")  # 80

# HPM 1.0 channel table
config = HPM10Config()
table = get_channel_table()
for ch in table[:3]:
    print(f"  CH{ch[\"id\"]}: {ch[\"ratio\"]} = {ch[\"frequency_hz\"]:.1f} Hz")

# Full HALE pipeline
pipeline = HALEPipeline(f0=16384.0, max_denominator=16)
result = pipeline.execute(divisors=[1, 2, 3, 4, 5])
print(f"Grid size: {result[\"grid_size\"]}")
```

---

## [PT-BR] Licença | [EN] License

Este projeto esta licenciado sob **CC BY 4.0**. Veja [LICENSE](LICENSE).

This project is licensed under **CC BY 4.0**. See [LICENSE](LICENSE).

> **Nota sobre Paper 1:** A equação HALE e referenciada do paper
> DOI: 10.5281/zenodo.18901934 (CC BY-NC-ND 4.0) unicamente como
> motivação teórica. Nenhum código foi derivado desse paper. A
> implementação e baseada no HPG 1.0 (DOI: 10.5281/zenodo.19056387,
> CC BY 4.0).

---

<div align="center">

**Hubstry Deep Tech** | Fundada em 2023 | Brasil

</div>