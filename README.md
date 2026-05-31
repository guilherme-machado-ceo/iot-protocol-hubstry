<div align="center">

# Nautam IoT Protocol

**HALE + HPG Framework: Harmonic Addressing and Protocol Grid for IoT**

[![DOI: HPG 1.0](https://zenodo.org/badge/DOI/10.5281/zenodo.19056387.svg)](https://doi.org/10.5281/zenodo.19056387)
[![DOI: HALE](https://zenodo.org/badge/DOI/10.5281/zenodo.18901934.svg)](https://doi.org/10.5281/zenodo.18901934)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![Demo](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://hubstry-harmonic-protocol.vercel.app/)
[![Site](https://img.shields.io/badge/site-nautam--iot-blue.svg)](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](hale_core/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](demo-web/harmonic-demo/)
[![Hubstry](https://img.shields.io/badge/by-Hubstry%20Deep%20Tech-0E8A7A.svg)](https://hubstry.dev)

> *A new communication standard for connected devices — built on the mathematics of sound.*
>
> *Um novo padrao de comunicacao para dispositivos conectados — construido sobre a matematica do som.*

</div>

---

## Incrementos / Latest Implementations | [PT-BR]

| Module | Arquivo / File | Descricao / Description |
|--------|---------------|------------------------|
| **HALE Pipeline** | `hale_core/hale_equation.py` | Pipeline: f0 -> H -> h -> psi -> c -> M -> g |
| **Funcoes psi1-psi4** | `hale_core/psi_functions.py` | 4 funcoes de enderecamento selecionaveis |
| **Omnigrid 2D** | `hpg_core/omnigrid.py` | Grade O_N = H_N x {-1, +1} com Euler |
| **HPM 1.0** | `hpg_core/hpm_config.py` | 12 canais harmonicos (f0 = 16.384 kHz) |
| **Sinal s(t) + FFT** | `hpg_core/signal_processing.py` | Sinal composto + decodificacao FFT |
| **Verificacao Espectral** | `hpg_core/spectral_verification.py` | Integridade de razoes racionais |
| **HSL Auth** | `security/hsl_auth.py` | H-Challenge/Response 3 etapas (~200B) |
| **Deteccao de Intrusao** | `security/intrusion_detection.py` | Desvio de fase Delta-phi > epsilon |
| **Rotacao LFSR** | `security/key_rotation.py` | Rotacao de chaves via LFSR |
| **Demo Web (Next.js 15)** | `demo-web/harmonic-demo/` | Dashboard interativo com React 19 + TailwindCSS 4 |

---

## [EN] What is Nautam?

Nautam is the commercial name for an IoT communication protocol based on the **harmonic series** — the same mathematical principle that governs how musical instruments produce sound. The underlying framework is the **HALE + HPG Framework** (Harmonic Addressing & Labeling Equation + Harmonic Protocol Grid).

Instead of devices competing for bandwidth (like 500 workers shouting in the same hallway), Nautam assigns each device its own precise communication slot derived mathematically from a master frequency — like an orchestra where every musician plays in perfect relationship to the conductor's beat.

**The result:**

- Native synchronization — no negotiation overhead
- Zero interference — mathematically guaranteed orthogonality
- 50–65% less energy consumption vs. conventional protocols (MQTT, CoAP, DDS)
- Runs on any hardware — pure software implementation, no specialized chips
- Infinitely scalable — adding a device is as simple as assigning a new harmonic

---

## [PT-BR] O que e o Nautam?

Nautam e o nome comercial de um protocolo de comunicacao IoT baseado na **serie harmonica** — o mesmo principio matematico que governa como instrumentos musicais produzem som. O framework subjacente e o **Framework HALE + HPG** (Harmonic Addressing & Labeling Equation + Harmonic Protocol Grid).

Em vez de dispositivos competirem por largura de banda (como 500 trabalhadores gritando no mesmo corredor), o Nautam atribui a cada dispositivo seu proprio slot de comunicacao preciso, derivado matematicamente a partir de uma frequencia mestra — como uma orquestra onde cada musico toca em relacao perfeita com a batida do regente.

**O resultado:**

- Sincronizacao nativa — sem sobrecarga de negociacao
- Interferencia zero — ortogonalidade matematicamente garantida
- 50–65% menos consumo de energia vs. protocolos convencionais (MQTT, CoAP, DDS)
- Roda em qualquer hardware — implementacao puramente em software, sem chips especializados
- Escalabilidade infinita — adicionar um dispositivo e tao simples quanto atribuir uma nova harmonica

---

## [EN] Architecture

```
iot-protocol-hubstry/
|
|-- demo-web/
|   |-- harmonic-demo/          # Interactive web dashboard
|       |-- app/                # Next.js 15 App Router
|       |-- components/         # React 19 components
|       |-- ...                 # TailwindCSS 4
|
|-- hale_core/                  # HALE - Harmonic Addressing & Latency Engine
|   |-- hale_equation.py        # Core pipeline: f0 -> H -> h -> psi -> c -> M -> g
|   |-- psi_functions.py        # 4 addressing functions (psi1-psi4)
|
|-- hpg_core/                   # HPG - Harmonic Protocol Grid
|   |-- omnigrid.py             # 2D Omnigrid: H_N x {-1, +1} with Euler totient
|   |-- hpm_config.py           # HPM 1.0 channel table (12 channels)
|   |-- signal_processing.py    # Composite signal s(t) + FFT decoding
|   |-- spectral_verification.py # Rational ratio integrity
|
|-- security/                   # HPG-Sec - Acoustic security layer
|   |-- hsl_auth.py             # H-Challenge/Response 3-step protocol (~200B)
|   |-- intrusion_detection.py  # Phase deviation detection
|   |-- key_rotation.py         # LFSR key rotation
|
|-- server/                     # Fastify API server (TypeScript)
|   |-- src/routes/             # API routes
|   |-- prisma/                 # Database schema (PostgreSQL)
|
|-- src/                        # C++ embedded implementation
|   |-- main.cpp                # Proof-of-concept
|   |-- security/               # PQC security layer
|
|-- docs/
|   |-- architecture.md          # 4-layer protocol architecture
|   |-- en/                     # English documentation
|   |-- pt/                     # Portuguese documentation
|
|-- LICENSE                     # CC BY 4.0
|-- README.md                   # This file
```

### Protocol layers | Camadas do Protocolo

| Layer | Name | EN Description | PT Descricao |
|-------|------|---------------|--------------|
| **L1** | HPG Core | Master frequency, harmonic slot assignment, orthogonality engine | Frequencia mestra, atribuicao de slots harmonicos, motor de ortogonalidade |
| **L2** | HPG Signal | Composite signal s(t), FFT decoding, spectral verification | Sinal composto s(t), decodificacao FFT, verificacao espectral |
| **L3** | HALE | Device addressing, latency management, synchronization via psi functions | Enderecamento de dispositivos, gerenciamento de latencia, sincronizacao via funcoes psi |
| **L4** | HPG-Sec | Timbral signature authentication, spectral intrusion detection, LFSR key rotation | Autenticacao por assinatura timbral, deteccao de intrusao espectral, rotacao de chaves LFSR |

---

## [EN] Mathematical Concepts

### Rational Harmonic Subdivision Set

H_N = { a/b in Q+ : gcd(a, b) = 1, b <= N, a <= N }

Cardinality: |H_N| = sum(phi(b)) for b = 1 to N, where phi is Euler's totient function.

Example: |H_16| = 80 unique channels.

### Omnigrid

O_N = H_N x {-1, +1}

|O_16| = 80 x 2 = 160 bidimensional addresses.

### Composite Signal

s(t) = sum A_k * sin(2 * pi * (a_k / b_k) * f0 * t + phi_k)

### Channel Priority

P(a/b) = 1 / (a + b)

### Resynchronization Period

T_sync = lcm(b1, b2, ...) / f0

---

## [PT-BR] Conceitos Matematicos

### Conjunto Harmonico Racional

H_N = { a/b em Q+ : gcd(a, b) = 1, b <= N, a <= N }

Cardinalidade: |H_N| = soma(phi(b)) para b = 1 ate N, onde phi e a funcao totiente de Euler.

Exemplo: |H_16| = 80 canais unicos.

### Omnigrid

O_N = H_N x {-1, +1}

|O_16| = 80 x 2 = 160 enderecos bidimensionais.

### Sinal Composto

s(t) = soma A_k * sin(2 * pi * (a_k / b_k) * f0 * t + phi_k)

### Prioridade de Canal

P(a/b) = 1 / (a + b)

### Periodo de Ressincronizacao

T_sync = mmc(b1, b2, ...) / f0

---

## [EN] Running the Demo

### Web Dashboard (Next.js 15)

```bash
git clone https://github.com/guilherme-machado-ceo/iot-protocol-hubstry.git
cd iot-protocol-hubstry/demo-web/harmonic-demo
npm install
npm run dev
```

Opens at **http://localhost:3000**

> Requires Node.js 18+ installed.

**Live demo:** [hubstry-harmonic-protocol.vercel.app](https://hubstry-harmonic-protocol.vercel.app/)

### Python Modules

```python
# No requirements.txt needed — core modules use only Python standard library
# Optional: pip install numpy  (for FFT in signal_processing.py)

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
    print(f"  CH{ch['id']}: {ch['ratio']} = {ch['frequency_hz']:.1f} Hz")

# Full HALE pipeline
pipeline = HALEPipeline(f0=16384.0, max_denominator=16)
result = pipeline.execute(divisors=[1, 2, 3, 4, 5])
print(f"Grid size: {result['grid_size']}")
```

---

## [PT-BR] Executando o Demo

### Dashboard Web (Next.js 15)

```bash
git clone https://github.com/guilherme-machado-ceo/iot-protocol-hubstry.git
cd iot-protocol-hubstry/demo-web/harmonic-demo
npm install
npm run dev
```

Abre em **http://localhost:3000**

> Requer Node.js 18+ instalado.

**Demo ao vivo:** [hubstry-harmonic-protocol.vercel.app](https://hubstry-harmonic-protocol.vercel.app/)

### Modulos Python

```python
# Nao e necessario requirements.txt — os modulos core usam apenas a biblioteca padrao
# Opcional: pip install numpy  (para FFT em signal_processing.py)

from hpg_core.omnigrid import compute_hn, cardinality_hn, omnigrid_2d
from hpg_core.hpm_config import HPM10Config, get_channel_table
from hpg_core.signal_processing import generate_composite_signal
from hale_core.hale_equation import HALEPipeline

# Calcular H_16
h16 = compute_hn(16)
print(f"|H_16| = {cardinality_hn(16)}")  # 80

# Tabela de canais HPM 1.0
config = HPM10Config()
table = get_channel_table()
for ch in table[:3]:
    print(f"  CH{ch['id']}: {ch['ratio']} = {ch['frequency_hz']:.1f} Hz")

# Pipeline HALE completo
pipeline = HALEPipeline(f0=16384.0, max_denominator=16)
result = pipeline.execute(divisors=[1, 2, 3, 4, 5])
print(f"Grid size: {result['grid_size']}")
```

---

## [EN] Scientific Foundation

The Nautam protocol is grounded in peer-reviewed research published on Zenodo:

| Publication | DOI | License | Description |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | General-purpose mathematical framework for complex systems |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Foundational specification of the HPG protocol family |

**Author:** Guilherme Goncalves Machado
**ORCID:** [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

---

## [PT-BR] Fundamentacao Cientifica

O protocolo Nautam e fundamentado em pesquisa revisada por pares publicada no Zenodo:

| Publicacao | DOI | Licenca | Descricao |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | Framework matematico de proposito geral para sistemas complexos |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Especificacao fundamental da familia de protocolos HPG |

**Autor:** Guilherme Goncalves Machado
**ORCID:** [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

---

## [EN] Protocol Family

Nautam is the commercial implementation of the HPG (Harmonic Protocol Grid) family:

| Variant | Focus | Status |
|---|---|---|
| **HPG-Core** | Base harmonic protocol | Active |
| **HPD-T** | Temperament-derived addressing (12-TET to Carrillo 96-tone) | Research |
| **HPG-R** | Humanoid robotics — harmonic hierarchy per body subsystem | Research |
| **HPG-Sec** | Acoustic cryptography — timbral PUF authentication | Research |
| **HPG-P** | Physical acoustics — inharmonic material signatures | Research |
| **HPG-D** | Pure digital / NCO implementation | Active |

---

## [PT-BR] Familia de Protocolos

Nautam e a implementacao comercial da familia HPG (Harmonic Protocol Grid):

| Variante | Foco | Status |
|---|---|---|
| **HPG-Core** | Protocolo harmonico base | Ativo |
| **HPD-T** | Enderecamento derivado de temperamento (12-TET ate Carrillo 96 tons) | Pesquisa |
| **HPG-R** | Robotica humanode — hierarquia harmonica por subsistema corporal | Pesquisa |
| **HPG-Sec** | Criptografia acustica — autenticacao PUF timbral | Pesquisa |
| **HPG-P** | Acustica fisica — assinaturas materiais inarmonicas | Pesquisa |
| **HPG-D** | Implementacao puramente digital / NCO | Ativo |

---

## [EN] Applications

- Smart cities — traffic, energy, water, waste sensor networks
- Industrial IoT — factory automation, predictive maintenance, logistics
- Robotics — harmonic hierarchy for humanoid subsystem coordination
- Security — physical unclonable functions via timbral signatures
- Transport infrastructure — railway monitoring, port automation

---

## [PT-BR] Aplicacoes

- Cidades inteligentes — redes de sensores de transito, energia, agua, residuos
- IoT industrial — automacao de fabricas, manutencao preditiva, logistica
- Robotica — hierarquia harmonica para coordenacao de subsistemas humanoides
- Seguranca — funcoes fisicamente inclonaveis via assinaturas timbrais
- Infraestrutura de transporte — monitoramento ferroviario, automacao portuaria

---

## [EN] Institutional Partnerships

| Partner | Program |
|---|---|
| Microsoft | Microsoft for Startups Founders Hub |
| Google | Google Cloud for Startups |
| GitHub / Google | Gemini via GitHub Education |
| Amazon | AWS Activate |
| AIIA | International Artificial Intelligence Industry Alliance (member since Jul 2025) |

---

## [PT-BR] Parcerias Institucionais

| Parceiro | Programa |
|---|---|
| Microsoft | Microsoft for Startups Founders Hub |
| Google | Google Cloud for Startups |
| GitHub / Google | Gemini via GitHub Education |
| Amazon | AWS Activate |
| AIIA | International Artificial Intelligence Industry Alliance (membro desde Jul 2025) |

---

## [EN] Hubstry Ecosystem | [PT-BR] Ecossistema Hubstry

This repository is part of the Hubstry ecosystem:

| Repository | Description | Link |
|---|---|---|
| **hubstry-security** | Cybersecurity platform with HSL and PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | HALE mathematical framework | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | IoT Protocol / HPG (this repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Qualia Hub Platform | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

Este repositorio faz parte do ecossistema Hubstry:

| Repositorio | Descricao | Link |
|---|---|---|
| **hubstry-security** | Plataforma de ciberseguranca com HSL e PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | Framework matematico HALE | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | Protocolo IoT / HPG (este repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Plataforma Qualia Hub | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

---

## [EN] License

This project is licensed under **CC BY 4.0**. See [LICENSE](LICENSE).

> **Note on Paper 1:** The HALE equation is referenced from
> DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) (CC BY 4.0)
> solely as theoretical motivation. The implementation is based on
> HPG 1.0 (DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387), CC BY 4.0).

---

## [PT-BR] Licenca

Este projeto esta licenciado sob **CC BY 4.0**. Veja [LICENSE](LICENSE).

> **Nota sobre Paper 1:** A equacao HALE e referenciada do paper
> DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) (CC BY 4.0)
> unicamente como motivacao teorica. A implementacao e baseada no
> HPG 1.0 (DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387), CC BY 4.0).

---

<div align="center">

**Nautam** by **Hubstry Deep Tech** | Fundada em 2023 | Brasil

Author: **Guilherme Goncalves Machado**
ORCID: [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

[hubstry.dev](https://hubstry.dev) | [Nautam site](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/) | guilhermemachado@hubstry.onmicrosoft.com

</div>
