# Nautam IoT Protocol — Streamlit POC Dashboard

Este diretório contém os módulos Python do protocolo Nautam (HALE + HPG Framework)
e um dashboard interativo Streamlit para visualização e execução do pipeline real.

## Estrutura

```
nautam-streamlit-poc/
├── hale_core/              # HALE — Harmonic Addressing & Labeling Equation
│   ├── __init__.py
│   ├── hale_equation.py    # Pipeline: f0 → H → h → ψ → c → M → g
│   └── psi_functions.py     # 4 funções de endereçamento (ψ1-ψ4)
├── hpg_core/               # HPG — Harmonic Protocol Grid
│   ├── __init__.py
│   ├── omnigrid.py         # Omnigrid 2D: H_N × {-1, +1}
│   ├── hpm_config.py       # HPM 1.0 (12 canais, f0=16.384 kHz)
│   ├── signal_processing.py # Sinal composto s(t) + FFT
│   └── spectral_verification.py # Verificação de integridade espectral
├── security/               # HPG-Sec — Camada de segurança
│   ├── __init__.py
│   ├── hsl_auth.py         # HSL Challenge/Response (~200B)
│   ├── intrusion_detection.py # Detecção por desvio de fase Δφ > ε
│   └── key_rotation.py     # LFSR Key Rotation
├── dashboard.py            # Streamlit dashboard interativo
└── requirements.txt        # Dependências Python
```

## Como Executar

```bash
# Na raiz do repo
cd iot-protocol-hubstry

# Instalar dependências
pip install -r nautam-streamlit-poc/requirements.txt

# Rodar o dashboard
streamlit run nautam-streamlit-poc/dashboard.py
```

Abre em **http://localhost:8501**

## Seções do Dashboard

| Seção | Descrição |
|-------|-----------|
| 📊 Visão Geral | Métricas, arquitetura 4 camadas, tabela HPM 1.0 |
| 🎵 HALE Pipeline | Pipeline interativo com seleção de função ψ |
| 📟 Omnigrid 2D | Visualização do grid bidimensional |
| 📡 Sinal + FFT | Geração de sinal composto e decodificação FFT |
| 🔐 Segurança (HSL) | Simulação do protocolo Challenge/Response |
| 🛡️ Detecção de Intrusão | Monitoramento de desvio de fase |
| 🔑 Rotação de Chaves | Geração de chaves via LFSR |
