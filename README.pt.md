# Protocolo IoT Nautam

[![Language: EN](https://img.shields.io/badge/lang-EN-blue.svg)](README.md) | **PT**

[![DOI: HPG 1.0](https://zenodo.org/badge/DOI/10.5281/zenodo.19056387.svg)](https://doi.org/10.5281/zenodo.19056387)
[![DOI: HALE](https://zenodo.org/badge/DOI/10.5281/zenodo.18901934.svg)](https://doi.org/10.5281/zenodo.18901934)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![Demo](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://hubstry-harmonic-protocol.vercel.app/)
[![Site](https://img.shields.io/badge/site-nautam--iot-blue.svg)](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](hale_core/)
[![Hubstry](https://img.shields.io/badge/by-Hubstry%20Deep%20Tech-0E8A7A.svg)](https://hubstry.dev)

> *A proxima geracao da comunicacao inteligente — construida sobre a matematica do som.*

---

## Incrementos Recentes

| Modulo | Arquivo | Descricao |
|--------|---------|-----------|
| **Pipeline HALE** | `hale_core/hale_equation.py` | Pipeline: f0 -> H -> h -> psi -> c -> M -> g |
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

## Visao Geral

O **Nautam IoT Protocol** (nome comercial do **Framework HALE + HPG**) e um protocolo de comunicacao IoT baseado na **serie harmonica** — o mesmo principio matematico que governa como instrumentos musicais produzem som.

Em vez de dispositivos competirem por largura de banda, o Nautam atribui a cada dispositivo seu proprio slot de comunicacao preciso, derivado matematicamente a partir de uma frequencia mestra — como uma orquestra onde cada musico toca em relacao perfeita com a batida do regente.

**O resultado:**

- Sincronizacao nativa — sem sobrecarga de negociacao
- Interferencia zero — ortogonalidade matematicamente garantida
- 50–65% menos consumo de energia vs. protocolos convencionais (MQTT, CoAP, DDS)
- Roda em qualquer hardware — implementacao puramente em software, sem chips especializados
- Escalabilidade infinita — adicionar um dispositivo e tao simples quanto atribuir uma nova harmonica

---

## Arquitetura

```
iot-protocol-hubstry/
|
|-- demo-web/
|   |-- harmonic-demo/          # Dashboard web interativo
|       |-- app/                # Next.js 15 App Router
|       |-- components/         # Componentes React 19
|       |-- ...                 # TailwindCSS 4
|
|-- hale_core/                  # HALE - Enderecamento Harmonico
|   |-- hale_equation.py        # Pipeline: f0 -> H -> h -> psi -> c -> M -> g
|   |-- psi_functions.py        # 4 funcoes de enderecamento (psi1-psi4)
|
|-- hpg_core/                   # HPG - Grade de Protocolo Harmonico
|   |-- omnigrid.py             # Omnigrid 2D: H_N x {-1, +1} com totiente de Euler
|   |-- hpm_config.py           # Tabela de canais HPM 1.0 (12 canais)
|   |-- signal_processing.py    # Sinal composto s(t) + decodificacao FFT
|   |-- spectral_verification.py # Integridade de razoes racionais
|
|-- security/                   # HPG-Sec - Camada de seguranca acustica
|   |-- hsl_auth.py             # H-Challenge/Response 3 etapas (~200B)
|   |-- intrusion_detection.py  # Deteccao por desvio de fase
|   |-- key_rotation.py         # Rotacao de chaves via LFSR
|
|-- server/                     # Servidor API Fastify (TypeScript)
|   |-- src/routes/             # Rotas da API
|   |-- prisma/                 # Schema do banco (PostgreSQL)
|
|-- src/                        # Implementacao embarcada em C++
|   |-- main.cpp                # Proof-of-concept
|   |-- security/               # Camada de seguranca PQC
|
|-- docs/
|   |-- architecture.md         # Arquitetura de 4 camadas
|   |-- en/                     # Documentacao em ingles
|   |-- pt/                     # Documentacao em portugues
```

### Camadas do Protocolo

| Camada | Nome | Descricao |
|--------|------|-----------|
| **L1** | HPG Core | Frequencia mestra, atribuicao de slots harmonicos, motor de ortogonalidade |
| **L2** | HPG Signal | Sinal composto s(t), decodificacao FFT, verificacao espectral |
| **L3** | HALE | Enderecamento de dispositivos, gerenciamento de latencia, sincronizacao via funcoes psi |
| **L4** | HPG-Sec | Autenticacao por assinatura timbral, deteccao de intrusao espectral, rotacao de chaves LFSR |

---

## Conceitos Matematicos

### Conjunto Harmonico Racional

H_N = { a/b em Q+ : gcd(a, b) = 1, b <= N, a <= N }

Cardinalidade: |H_N| = soma(phi(b)) para b = 1 ate N

Onde phi(b) e a funcao totiente de Euler.

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

## Executando o Demo

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

## Fundamentacao Cientifica

O protocolo Nautam e fundamentado em pesquisa revisada por pares publicada no Zenodo:

| Publicacao | DOI | Licenca | Descricao |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | Framework matematico de proposito geral para sistemas complexos |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Especificacao fundamental da familia de protocolos HPG |

**Autor:** Guilherme Goncalves Machado
**ORCID:** [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

---

## Familia de Protocolos

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

## Aplicacoes

- Cidades inteligentes — redes de sensores de transito, energia, agua, residuos
- IoT industrial — automacao de fabricas, manutencao preditiva, logistica
- Robotica — hierarquia harmonica para coordenacao de subsistemas humanoides
- Seguranca — funcoes fisicamente inclonaveis via assinaturas timbrais
- Infraestrutura de transporte — monitoramento ferroviario, automacao portuaria

---

## Parcerias Institucionais

| Parceiro | Programa |
|---|---|
| Microsoft | Microsoft for Startups Founders Hub |
| Google | Google Cloud for Startups |
| GitHub / Google | Gemini via GitHub Education |
| Amazon | AWS Activate |
| AIIA | International Artificial Intelligence Industry Alliance (membro desde Jul 2025) |

---

## Ecossistema Hubstry

Este repositorio faz parte do ecossistema Hubstry:

| Repositorio | Descricao | Link |
|---|---|---|
| **hubstry-security** | Plataforma de ciberseguranca com HSL e PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | Framework matematico HALE | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | Protocolo IoT / HPG (este repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Plataforma Qualia Hub | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

---

## Licenca

Este projeto esta licenciado sob **CC BY 4.0**. Veja [LICENSE](LICENSE).

> **Nota sobre Paper 1:** A equacao HALE e referenciada do paper
> DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) (CC BY 4.0)
> unicamente como motivacao teorica. A implementacao e baseada no
> HPG 1.0 (DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387), CC BY 4.0).

---

<div align="center">

**Nautam** por **Hubstry Deep Tech** | Fundada em 2023 | Brasil

Autor: **Guilherme Goncalves Machado**
ORCID: [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

[hubstry.dev](https://hubstry.dev) | [Site Nautam](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/) | guilhermemachado@hubstry.onmicrosoft.com

</div>
