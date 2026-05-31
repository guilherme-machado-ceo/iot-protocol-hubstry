<div align="center">

# Nautam IoT Protocol

**HALE + HPG Framework: Harmonic Addressing and Protocol Grid for IoT**

[![DOI: HPG 1.0](https://img.shields.io/badge/DOI-10.5281/zenodo.19056387-blue.svg)](https://doi.org/10.5281/zenodo.19056387)
[![DOI: HALE](https://img.shields.io/badge/DOI-10.5281/zenodo.18901934-blue.svg)](https://doi.org/10.5281/zenodo.18901934)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![Site](https://img.shields.io/badge/site-nautam--iot-blue.svg)](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](hale_core/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](dashboard.py)
[![Next.js 15](https://img.shields.io/badge/Sim_Web-Next.js_15-black.svg)](demo-web/harmonic-demo/)
[![Hubstry](https://img.shields.io/badge/by-Hubstry%20Deep%20Tech-0E8A7A.svg)](https://hubstry.dev)

> *A new communication standard for connected devices — built on the mathematics of sound.*
>
> *Um novo padrão de comunicação para dispositivos conectados — construído sobre a matemática do som.*

</div>

---

## Incrementos / Latest Implementations | [PT-BR]

| Module | Arquivo / File | Descrição / Description |
|--------|---------------|------------------------|
| **HALE Pipeline** | `hale_core/hale_equation.py` | Pipeline: f0 → H → h → ψ → c → M → g |
| **Funções ψ1-ψ4** | `hale_core/psi_functions.py` | 4 funções de endereçamento selecionáveis |
| **Omnigrid 2D** | `hpg_core/omnigrid.py` | Grade O_N = H_N × {-1, +1} com Euler |
| **HPM 1.0** | `hpg_core/hpm_config.py` | 12 canais harmônicos (f0 = 16.384 kHz) |
| **Sinal s(t) + FFT** | `hpg_core/signal_processing.py` | Sinal composto + decodificação FFT |
| **Verificação Espectral** | `hpg_core/spectral_verification.py` | Integridade de razões racionais |
| **HSL Auth** | `security/hsl_auth.py` | H-Challenge/Response 3 etapas (~200B) |
| **Detecção de Intrusão** | `security/intrusion_detection.py` | Desvio de fase Δφ > ε |
| **Rotação LFSR** | `security/key_rotation.py` | Rotação de chaves via LFSR |
| **Dashboard (Streamlit)** | `dashboard.py` | Dashboard interativo — pipeline real com 7 seções |
| **Demo Web (Next.js 15)** | `demo-web/harmonic-demo/` | Simulação visual com React 19 + TailwindCSS 4 |

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

## [PT-BR] O que é o Nautam?

Nautam é o nome comercial de um protocolo de comunicação IoT baseado na **série harmônica** — o mesmo princípio matemático que governa como instrumentos musicais produzem som. O framework subjacente é o **Framework HALE + HPG** (Harmonic Addressing & Labeling Equation + Harmonic Protocol Grid).

Em vez de dispositivos competirem por largura de banda (como 500 trabalhadores gritando no mesmo corredor), o Nautam atribui a cada dispositivo seu próprio slot de comunicação preciso, derivado matematicamente a partir de uma frequência mestra — como uma orquestra onde cada músico toca em relação perfeita com a batida do regente.

**O resultado:**

- Sincronização nativa — sem sobrecarga de negociação
- Interferência zero — ortogonalidade matematicamente garantida
- 50–65% menos consumo de energia vs. protocolos convencionais (MQTT, CoAP, DDS)
- Roda em qualquer hardware — implementação puramente em software, sem chips especializados
- Escalabilidade infinita — adicionar um dispositivo é tão simples quanto atribuir uma nova harmônica

---

## [EN] Architecture

```
iot-protocol-hubstry/
│
├── dashboard.py                 # Streamlit interactive dashboard (real pipeline)
├── requirements.txt             # Python dependencies (streamlit, numpy, plotly)
│
├── demo-web/
│   └── harmonic-demo/          # Visual simulation dashboard
│       ├── app/                # Next.js 15 App Router
│       ├── components/         # React 19 components
│       └── ...                 # TailwindCSS 4
│
├── hale_core/                  # HALE - Harmonic Addressing & Latency Engine
│   ├── hale_equation.py        # Core pipeline: f0 → H → h → ψ → c → M → g
│   └── psi_functions.py        # 4 addressing functions (ψ1-ψ4)
│
├── hpg_core/                   # HPG - Harmonic Protocol Grid
│   ├── omnigrid.py             # 2D Omnigrid: H_N × {-1, +1} with Euler totient
│   ├── hpm_config.py           # HPM 1.0 channel table (12 channels)
│   ├── signal_processing.py    # Composite signal s(t) + FFT decoding
│   └── spectral_verification.py # Rational ratio integrity
│
├── security/                   # HPG-Sec - Acoustic security layer
│   ├── hsl_auth.py             # H-Challenge/Response 3-step protocol (~200B)
│   ├── intrusion_detection.py  # Phase deviation detection
│   └── key_rotation.py         # LFSR key rotation
│
├── docs/
│   ├── architecture.md         # 4-layer protocol architecture
│   ├── en/                     # English documentation
│   └── pt/                     # Portuguese documentation
│
├── LICENSE                     # CC BY 4.0
└── README.md                   # This file
```

### Protocol layers | Camadas do Protocolo

| Layer | Name | EN Description | PT Descrição |
|-------|------|---------------|-------------|
| **L1** | HPG Core | Master frequency, harmonic slot assignment, orthogonality engine | Frequência mestra, atribuição de slots harmônicos, motor de ortogonalidade |
| **L2** | HPG Signal | Composite signal s(t), FFT decoding, spectral verification | Sinal composto s(t), decodificação FFT, verificação espectral |
| **L3** | HALE | Device addressing, latency management, synchronization via ψ functions | Endereçamento de dispositivos, gerenciamento de latência, sincronização via funções ψ |
| **L4** | HPG-Sec | Timbral signature authentication, spectral intrusion detection, LFSR key rotation | Autenticação por assinatura timbral, detecção de intrusão espectral, rotação de chaves LFSR |

---

## [EN] Mathematical Concepts

### Rational Harmonic Subdivision Set

H_N = { a/b ∈ Q⁺ : gcd(a, b) = 1, b ≤ N, a ≤ N }

Cardinality: |H_N| = Σ φ(b) for b = 1 to N, where φ is Euler's totient function.

Example: |H_16| = 80 unique channels.

### Omnigrid

O_N = H_N × {-1, +1}

|O_16| = 80 × 2 = 160 bidimensional addresses.

### Composite Signal

s(t) = Σ Aₖ sin(2π(aₖ/bₖ)f₀t + φₖ)

### Channel Priority

P(a/b) = 1 / (a + b)

### Resynchronization Period

T_sync = lcm(b₁, b₂, ...) / f₀

---

## [PT-BR] Conceitos Matemáticos

### Conjunto Harmônico Racional

H_N = { a/b ∈ Q⁺ : gcd(a, b) = 1, b ≤ N, a ≤ N }

Cardinalidade: |H_N| = Σ φ(b) para b = 1 até N, onde φ é a função totiente de Euler.

Exemplo: |H_16| = 80 canais únicos.

### Omnigrid

O_N = H_N × {-1, +1}

|O_16| = 80 × 2 = 160 endereços bidimensionais.

### Sinal Composto

s(t) = Σ Aₖ sin(2π(aₖ/bₖ)f₀t + φₖ)

### Prioridade de Canal

P(a/b) = 1 / (a + b)

### Período de Ressincronização

T_sync = mmc(b₁, b₂, ...) / f₀

---

## [EN] Running the Protocol

### Interactive Dashboard (Streamlit) — Real Pipeline

The Streamlit dashboard executes the **actual HALE + HPG pipeline** in real time — no mock data, no simulation. Every computation (harmonic grid, signal generation, FFT decoding, authentication, intrusion detection) uses the real formulas published in the Zenodo papers.

```bash
git clone https://github.com/guilherme-machado-ceo/iot-protocol-hubstry.git
cd iot-protocol-hubstry
pip install -r requirements.txt
streamlit run dashboard.py
```

Opens at **http://localhost:8501** — the dashboard opens automatically in your browser.

> Requires Python 3.10+ installed.

**Dashboard sections (7 interactive modules):**

| Section | What it does |
|---------|-------------|
| Visão Geral | Protocol overview: H_N cardinality, O_N addresses, 4-layer architecture |
| HALE Pipeline | Full pipeline f₀ → H → h → ψ → c → M → g with selectable ψ functions |
| Omnigrid 2D | 2D address space O_N = H_N × {-1, +1} visualization |
| Sinal Composto + FFT | Real composite signal s(t) generation + FFT spectral decoding |
| Segurança (HSL) | HSL Challenge/Response authentication protocol (~200 bytes) |
| Detecção de Intrusão | Phase deviation intrusion detection (Δφ > ε) |
| Rotação de Chaves (LFSR) | LFSR-based cryptographic key rotation engine |

See [README_DASHBOARD.md](README_DASHBOARD.md) for full dashboard documentation.

**Nautam site:** [nautam-iot-protocol-site](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)

### Visual Simulation (Next.js 15)

> **Important:** The Next.js web dashboard is a **visual simulation** of the harmonic protocol concept — designed for investor presentations and marketing materials. It displays mock data (metrics, channel activity) and does **not** execute the actual HALE/HPG pipeline. For the real protocol, use the Streamlit dashboard above.

```bash
cd iot-protocol-hubstry/demo-web/harmonic-demo
npm install
npm run dev
```

Opens at **http://localhost:3000**

> Requires Node.js 18+ installed.

### Python Modules (Programmatic API)

The core modules can also be used directly in Python code — no Streamlit required:

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
    print(f"  CH{ch['id']}: {ch['ratio']} = {ch['frequency_hz']:.1f} Hz")

# Full HALE pipeline
pipeline = HALEPipeline(f0=16384.0, max_denominator=16)
result = pipeline.execute(divisors=[1, 2, 3, 4, 5])
print(f"Grid size: {result.grid_size}")
print(f"Omnigrid addresses: {result.omnigrid_size}")
print(f"Resync period: {result.resync_period * 1000:.4f} ms")
```

---

## [PT-BR] Executando o Protocolo

### Dashboard Interativo (Streamlit) — Pipeline Real

O dashboard Streamlit executa o **pipeline HALE + HPG real** em tempo real — sem dados simulados, sem mock. Cada computação (grade harmônica, geração de sinal, decodificação FFT, autenticação, detecção de intrusão) usa as fórmulas reais publicadas nos papers Zenodo.

```bash
git clone https://github.com/guilherme-machado-ceo/iot-protocol-hubstry.git
cd iot-protocol-hubstry
pip install -r requirements.txt
streamlit run dashboard.py
```

Abre em **http://localhost:8501** — o dashboard abre automaticamente no navegador.

> Requer Python 3.10+ instalado.

**Seções do dashboard (7 módulos interativos):**

| Seção | O que faz |
|-------|-----------|
| Visão Geral | Visão geral do protocolo: cardinalidade H_N, endereços O_N, arquitetura 4 camadas |
| HALE Pipeline | Pipeline completa f₀ → H → h → ψ → c → M → g com funções ψ selecionáveis |
| Omnigrid 2D | Visualização do espaço de endereços 2D O_N = H_N × {-1, +1} |
| Sinal Composto + FFT | Geração real do sinal composto s(t) + decodificação espectral FFT |
| Segurança (HSL) | Protocolo de autenticação HSL Challenge/Response (~200 bytes) |
| Detecção de Intrusão | Detecção de intrusão por desvio de fase (Δφ > ε) |
| Rotação de Chaves (LFSR) | Motor de rotação de chaves criptográficas via LFSR |

Veja [README_DASHBOARD.md](README_DASHBOARD.md) para documentação completa do dashboard.

**Site Nautam:** [nautam-iot-protocol-site](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)

### Simulação Visual (Next.js 15)

> **Importante:** O dashboard web Next.js é uma **simulação visual** do conceito do protocolo harmônico — projetado para apresentações a investidores e materiais de marketing. Exibe dados simulados (métricas, atividade de canais) e **não** executa o pipeline HALE/HPG real. Para o protocolo real, use o dashboard Streamlit acima.

```bash
cd iot-protocol-hubstry/demo-web/harmonic-demo
npm install
npm run dev
```

Abre em **http://localhost:3000**

> Requer Node.js 18+ instalado.

### Módulos Python (API Programática)

Os módulos core também podem ser usados diretamente em código Python — sem necessidade do Streamlit:

```python
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
print(f"Grid size: {result.grid_size}")
print(f"Endereços Omnigrid: {result.omnigrid_size}")
print(f"Período de ressync: {result.resync_period * 1000:.4f} ms")
```

---

## [EN] Scientific Foundation

The Nautam protocol is grounded in peer-reviewed research published on Zenodo:

| Publication | DOI | License | Description |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | General-purpose mathematical framework for complex systems |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Foundational specification of the HPG protocol family |

**Author:** Guilherme Gonçalves Machado
**ORCID:** [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

---

## [PT-BR] Fundamentação Científica

O protocolo Nautam é fundamentado em pesquisa revisada por pares publicada no Zenodo:

| Publicação | DOI | Licença | Descrição |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | Framework matemático de propósito geral para sistemas complexos |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Especificação fundamental da família de protocolos HPG |

**Autor:** Guilherme Gonçalves Machado
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

## [PT-BR] Família de Protocolos

Nautam é a implementação comercial da família HPG (Harmonic Protocol Grid):

| Variante | Foco | Status |
|---|---|---|
| **HPG-Core** | Protocolo harmônico base | Ativo |
| **HPD-T** | Endereçamento derivado de temperamento (12-TET até Carrillo 96 tons) | Pesquisa |
| **HPG-R** | Robótica humanoide — hierarquia harmônica por subsistema corporal | Pesquisa |
| **HPG-Sec** | Criptografia acústica — autenticação PUF timbral | Pesquisa |
| **HPG-P** | Acústica física — assinaturas materiais inarmônicas | Pesquisa |
| **HPG-D** | Implementação puramente digital / NCO | Ativo |

---

## [EN] Applications

- Smart cities — traffic, energy, water, waste sensor networks
- Industrial IoT — factory automation, predictive maintenance, logistics
- Robotics — harmonic hierarchy for humanoid subsystem coordination
- Security — physical unclonable functions via timbral signatures
- Transport infrastructure — railway monitoring, port automation

---

## [PT-BR] Aplicações

- Cidades inteligentes — redes de sensores de trânsito, energia, água, resíduos
- IoT industrial — automação de fábricas, manutenção preditiva, logística
- Robótica — hierarquia harmônica para coordenação de subsistemas humanoides
- Segurança — funções fisicamente inclonáveis via assinaturas timbrais
- Infraestrutura de transporte — monitoramento ferroviário, automação portuária

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

Este repositório faz parte do ecossistema Hubstry:

| Repositório | Descrição | Link |
|---|---|---|
| **hubstry-security** | Plataforma de cibersegurança com HSL e PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | Framework matemático HALE | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
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

## [PT-BR] Licença

Este projeto está licenciado sob **CC BY 4.0**. Veja [LICENSE](LICENSE).

> **Nota sobre Paper 1:** A equação HALE é referenciada do paper
> DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) (CC BY 4.0)
> unicamente como motivação teórica. A implementação é baseada no
> HPG 1.0 (DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387), CC BY 4.0).

---

<div align="center">

**Nautam** by **Hubstry Deep Tech** | Fundada em 2023 | Brasil

Autor: **Guilherme Gonçalves Machado**
ORCID: [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

[hubstry.dev](https://hubstry.dev) | [Nautam site](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/) | guilhermemachado@hubstry.onmicrosoft.com

</div>
