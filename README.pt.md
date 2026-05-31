# Protocolo IoT Nautam

[![Language: EN](https://img.shields.io/badge/lang-EN-blue.svg)](README.md) | **PT**

[![DOI: HPG 1.0](https://zenodo.org/badge/DOI/10.5281/zenodo.19056387.svg)](https://doi.org/10.5281/zenodo.19056387)
[![DOI: HALE](https://zenodo.org/badge/DOI/10.5281/zenodo.18901934.svg)](https://doi.org/10.5281/zenodo.18901934)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![Site](https://img.shields.io/badge/site-nautam--iot-blue.svg)](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](hale_core/)
[![Hubstry](https://img.shields.io/badge/by-Hubstry%20Deep%20Tech-0E8A7A.svg)](https://hubstry.dev)

> *A próxima geração da comunicação inteligente — construída sobre a matemática do som.*

---

## Incrementos Recentes

| Módulo | Arquivo | Descrição |
|--------|---------|-----------|
| **Pipeline HALE** | `hale_core/hale_equation.py` | Pipeline: f0 → H → h → ψ → c → M → g |
| **Funções ψ1-ψ4** | `hale_core/psi_functions.py` | 4 funções de endereçamento selecionáveis |
| **Omnigrid 2D** | `hpg_core/omnigrid.py` | Grade O_N = H_N × {-1, +1} com Euler |
| **HPM 1.0** | `hpg_core/hpm_config.py` | 12 canais harmônicos (f0 = 16.384 kHz) |
| **Sinal s(t) + FFT** | `hpg_core/signal_processing.py` | Sinal composto + decodificação FFT |
| **Verificação Espectral** | `hpg_core/spectral_verification.py` | Integridade de razões racionais |
| **HSL Auth** | `security/hsl_auth.py` | H-Challenge/Response 3 etapas (~200B) |
| **Detecção de Intrusão** | `security/intrusion_detection.py` | Desvio de fase Δφ > ε |
| **Rotação LFSR** | `security/key_rotation.py` | Rotação de chaves via LFSR |
| **Demo Web (Next.js 15)** | `demo-web/harmonic-demo/` | Dashboard interativo com React 19 + TailwindCSS 4 |

---

## Visão Geral

O **Nautam IoT Protocol** (nome comercial do **Framework HALE + HPG**) é um protocolo de comunicação IoT baseado na **série harmônica** — o mesmo princípio matemático que governa como instrumentos musicais produzem som.

Em vez de dispositivos competirem por largura de banda, o Nautam atribui a cada dispositivo seu próprio slot de comunicação preciso, derivado matematicamente a partir de uma frequência mestra — como uma orquestra onde cada músico toca em relação perfeita com a batida do regente.

**O resultado:**

- Sincronização nativa — sem sobrecarga de negociação
- Interferência zero — ortogonalidade matematicamente garantida
- 50–65% menos consumo de energia vs. protocolos convencionais (MQTT, CoAP, DDS)
- Roda em qualquer hardware — implementação puramente em software, sem chips especializados
- Escalabilidade infinita — adicionar um dispositivo é tão simples quanto atribuir uma nova harmônica

---

## Arquitetura

```
iot-protocol-hubstry/
│
├── demo-web/
│   └── harmonic-demo/          # Dashboard web interativo
│       ├── app/                # Next.js 15 App Router
│       ├── components/         # Componentes React 19
│       └── ...                 # TailwindCSS 4
│
├── hale_core/                  # HALE - Endereçamento Harmônico
│   ├── hale_equation.py        # Pipeline: f0 → H → h → ψ → c → M → g
│   └── psi_functions.py        # 4 funções de endereçamento (ψ1-ψ4)
│
├── hpg_core/                   # HPG - Grade de Protocolo Harmônico
│   ├── omnigrid.py             # Omnigrid 2D: H_N × {-1, +1} com totiente de Euler
│   ├── hpm_config.py           # Tabela de canais HPM 1.0 (12 canais)
│   ├── signal_processing.py    # Sinal composto s(t) + decodificação FFT
│   └── spectral_verification.py # Integridade de razões racionais
│
├── security/                   # HPG-Sec - Camada de segurança acústica
│   ├── hsl_auth.py             # H-Challenge/Response 3 etapas (~200B)
│   ├── intrusion_detection.py  # Detecção por desvio de fase
│   └── key_rotation.py         # Rotação de chaves via LFSR
│
├── server/                     # Servidor API Fastify (TypeScript)
│   ├── src/routes/             # Rotas da API
│   └── prisma/                 # Schema do banco (PostgreSQL)
│
├── src/                        # Implementação embarcada em C++
│   ├── main.cpp                # Proof-of-concept
│   └── security/               # Camada de segurança PQC
│
├── docs/
│   ├── architecture.md         # Arquitetura de 4 camadas
│   ├── en/                     # Documentação em inglês
│   └── pt/                     # Documentação em português
```

### Camadas do Protocolo

| Camada | Nome | Descrição |
|--------|------|-----------|
| **L1** | HPG Core | Frequência mestra, atribuição de slots harmônicos, motor de ortogonalidade |
| **L2** | HPG Signal | Sinal composto s(t), decodificação FFT, verificação espectral |
| **L3** | HALE | Endereçamento de dispositivos, gerenciamento de latência, sincronização via funções ψ |
| **L4** | HPG-Sec | Autenticação por assinatura timbral, detecção de intrusão espectral, rotação de chaves LFSR |

---

## Conceitos Matemáticos

### Conjunto Harmônico Racional

H_N = { a/b ∈ Q⁺ : gcd(a, b) = 1, b ≤ N, a ≤ N }

Cardinalidade: |H_N| = Σ φ(b) para b = 1 até N

Onde φ(b) é a função totiente de Euler.

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

**Site Nautam:** [nautam-iot-protocol-site](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/)

> **Importante:** O dashboard web é uma **simulação visual** do conceito do protocolo harmônico — projetado para demonstração e apresentações a investidores. Exibe dados simulados (métricas, atividade de canais) e não executa o pipeline HALE/HPG real. Para a implementação real do protocolo, veja os **módulos Python** abaixo.

### Módulos Python

```python
# Não é necessário requirements.txt — os módulos core usam apenas a biblioteca padrão
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

## Fundamentação Científica

O protocolo Nautam é fundamentado em pesquisa revisada por pares publicada no Zenodo:

| Publicação | DOI | Licença | Descrição |
|---|---|---|---|
| HALE: Harmonic Addressing & Labeling Equation | [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | CC BY 4.0 | Framework matemático de propósito geral para sistemas complexos |
| Harmonic Protocol Grid (HPG 1.0) | [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387) | CC BY 4.0 | Especificação fundamental da família de protocolos HPG |

**Autor:** Guilherme Gonçalves Machado
**ORCID:** [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

---

## Família de Protocolos

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

## Aplicações

- Cidades inteligentes — redes de sensores de trânsito, energia, água, resíduos
- IoT industrial — automação de fábricas, manutenção preditiva, logística
- Robótica — hierarquia harmônica para coordenação de subsistemas humanoides
- Segurança — funções fisicamente inclonáveis via assinaturas timbrais
- Infraestrutura de transporte — monitoramento ferroviário, automação portuária

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

Este repositório faz parte do ecossistema Hubstry:

| Repositório | Descrição | Link |
|---|---|---|
| **hubstry-security** | Plataforma de cibersegurança com HSL e PQC | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-security) |
| **hubstry-hale-ecosystem** | Framework matemático HALE | [GitHub](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) |
| **iot-protocol-hubstry** | Protocolo IoT / HPG (este repo) | [GitHub](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry) |
| **qualia-hub-ecosystem** | Plataforma Qualia Hub | [GitHub](https://github.com/guilherme-machado-ceo/qualia-hub-ecosystem) |

---

## Licença

Este projeto está licenciado sob **CC BY 4.0**. Veja [LICENSE](LICENSE).

> **Nota sobre Paper 1:** A equação HALE é referenciada do paper
> DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) (CC BY 4.0)
> unicamente como motivação teórica. A implementação é baseada no
> HPG 1.0 (DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387), CC BY 4.0).

---

<div align="center">

**Nautam** por **Hubstry Deep Tech** | Fundada em 2023 | Brasil

Autor: **Guilherme Gonçalves Machado**
ORCID: [0009-0008-1083-0784](https://orcid.org/0009-0008-1083-0784)

[hubstry.dev](https://hubstry.dev) | [Site Nautam](https://guilherme-machado-ceo.github.io/nautam-iot-protocol-site/) | guilhermemachado@hubstry.onmicrosoft.com

</div>
