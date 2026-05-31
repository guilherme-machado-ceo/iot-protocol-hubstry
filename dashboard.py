"""Nautam IoT Protocol — Interactive Dashboard (Executive Edition).

Streamlit dashboard that executes the real HALE + HPG pipeline
and visualizes harmonic protocol operations.

Includes executive-friendly explanations for C-level / government audiences.

Usage:
    cd iot-protocol-hubstry
    streamlit run dashboard.py

Opens at http://localhost:8501
"""

import hashlib
import secrets
import time
from collections import Counter

import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from hale_core.hale_equation import HALEPipeline, HALEPipelineResult
from hale_core.psi_functions import euler_totient, psi1, psi2, psi3, psi4
from hpg_core.omnigrid import compute_hn, cardinality_hn, omnigrid_2d
from hpg_core.hpm_config import HPM10Config, get_channel_table
from hpg_core.signal_processing import generate_composite_signal, decode_fft
from hpg_core.spectral_verification import verify_rational_integrity, SpectralReport
from security.hsl_auth import HSLAuth, HSLChallenge
from security.intrusion_detection import IntrusionDetector, IntrusionReport
from security.key_rotation import LFSRKeyRotation

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Nautam IoT Protocol — Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #0a0f1a 0%, #1a1040 100%);
        border: 1px solid #2a2a5a;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00ffff;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8888aa;
        margin-top: 4px;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #0d1a2a 100%);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #00ffff;
        border-bottom: 2px solid #00ffff;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    .exec-box {
        background: #000000;
        border-left: 4px solid #00ffff;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 8px 0 16px 0;
        color: #ffffff;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .exec-box strong {
        color: #00ffff;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────

if "auth_system" not in st.session_state:
    st.session_state.auth_system = HSLAuth()
if "key_rotation" not in st.session_state:
    st.session_state.key_rotation = LFSRKeyRotation(seed=secrets.randbits(16))
if "auth_log" not in st.session_state:
    st.session_state.auth_log = []

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.shields.io/badge/by-Hubstry%20Deep%20Tech-0E8A7A.svg", width=200)
    st.markdown("## Nautam IoT Protocol")
    st.markdown("---")
    st.markdown("**Dashboard POC** — executa o pipeline real HALE + HPG.")

    st.markdown("---")
    st.markdown("### Navegação / Navigation")
    page = st.radio(
        "Seção",
        [
            "📊 Visão Geral",
            "🎵 HALE Pipeline",
            "📟 Omnigrid 2D",
            "📡 Sinal Composto + FFT",
            "🔐 Segurança (HSL)",
            "🛡️ Detecção de Intrusão",
            "🔑 Rotação de Chaves (LFSR)",
        ],
    )

    st.markdown("---")
    st.markdown("### Parâmetros Globais / Global Parameters")
    global_f0 = st.number_input(
        "Frequência Fundamental f₀ (Hz)",
        min_value=100.0,
        max_value=100000.0,
        value=16384.0,
        step=1.0,
        key="global_f0",
    )
    global_N = st.slider("Denominador Máximo N", 2, 64, 16, key="global_N")

    st.markdown("---")

    # ── Para Decisores ──
    st.markdown("### 📋 Resumo Executivo")
    st.markdown(
        """
<div style='background: linear-gradient(135deg, #0d2137 0%, #0a1628 100%);
border-left: 4px solid #00ffff; border-radius: 0 12px 12px 0;
padding: 12px 16px; font-size: 0.92rem; color: #ffffff;'>
<strong style='color: #00ffff;'>O que é este dashboard?</strong><br><br>
Este painel executa a <strong>tecnologia real</strong> do protocolo Nautam
em tempo real — a mesma matemática que será implantada em
cidades inteligentes, indústrias e infraestrutura governamental.<br><br>
Navegue pelas seções para ver cada camada do protocolo em ação:
endereçamento, comunicação, autenticação e segurança.
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<small style='color: #999;'>"
        "DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | "
        "DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387)"
        "</small>",
        unsafe_allow_html=True,
    )

# ─── Main Content ─────────────────────────────────────────────────────────────

st.title("🌊 Nautam IoT Protocol — Dashboard")
st.caption("HALE + HPG Framework | Pipeline real em Python")
st.markdown(
    "<div class='exec-box'>"
    "<strong>Contexto:</strong> Este dashboard executa o protocolo Nautam "
    "em tempo real. Cada computação usa as fórmulas publicadas nos papers "
    "científicos (DOI: 18901934, 19056387). Não é uma simulação — é a "
    "tecnologia real executável. / "
    "This dashboard executes the Nautam protocol in real time. Every computation "
    "uses the formulas published in peer-reviewed papers. Not a simulation — "
    "it is the actual, executable technology."
    "</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 0: Overview
# ═══════════════════════════════════════════════════════════════════════════════

if page == "📊 Visão Geral":
    st.header("Visão Geral do Protocolo / Protocol Overview")

    with st.expander("📖 O que esta seção mostra? / What does this section show?"):
        st.markdown(
            """
**PT-BR:** Visão geral do protocolo Nautam. As métricas mostram a capacidade
de endereçamento e comunicação do protocolo. **Canais H_N** são os slots de
comunicação disponíveis (cada dispositivo IoT recebe um slot único).
**Endereços O_N** dobram essa capacidade usando polaridade (+/-).
**Canais HPM 1.0** são os 12 canais-padrão para implantação inicial.
**f₀** é a frequência mestra que sincroniza toda a rede.

**EN:** Overview of the Nautam protocol. The metrics show the addressing and
communication capacity. **H_N Channels** are unique communication slots (each
IoT device gets its own). **O_N Addresses** double the capacity using polarity.
**HPM 1.0 Channels** are the 12 standard channels for initial deployment.
**f₀** is the master frequency that synchronizes the entire network.
            """
        )

    # Quick metrics
    col1, col2, col3, col4 = st.columns(4)
    cardinality = cardinality_hn(global_N)
    table = get_channel_table()
    t_sync = global_f0 / cardinality if cardinality > 0 else 0

    with col1:
        st.metric("Canais H_N", cardinality)
        st.caption("Slots de comunicação únicos")
    with col2:
        st.metric("Endereços O_N", cardinality * 2)
        st.caption("Capacidade dobrada (polaridade)")
    with col3:
        st.metric("Canais HPM 1.0", len(table))
        st.caption("Canais padrão de implantação")
    with col4:
        st.metric("f₀ (Hz)", f"{global_f0:,.0f}")
        st.caption("Frequência mestra da rede")

    st.markdown("---")

    # Architecture diagram
    st.subheader("Arquitetura — 4 Camadas / Architecture — 4 Layers")

    with st.expander("📖 Como funciona a arquitetura? / How does the architecture work?"):
        st.markdown(
            """
**PT-BR:** O protocolo opera em 4 camadas sobrepostas:
- **L1 — Grid:** Base matemática que gera os endereços para cada dispositivo.
- **L2 — Sinal:** Transforma endereços em sinais físicos (ondas harmônicas).
- **L3 — Endereçamento (HALE):** Pipeline completa de atribuição automática de endereço.
- **L4 — Segurança:** Autenticação, detecção de invasão e rotação de chaves.

**EN:** The protocol operates in 4 stacked layers:
- **L1 — Grid:** Mathematical base generating addresses for each device.
- **L2 — Signal:** Transforms addresses into physical signals (harmonic waves).
- **L3 — Addressing (HALE):** Full automatic address assignment pipeline.
- **L4 — Security:** Authentication, intrusion detection, and key rotation.
            """
        )

    layers = [
        {"camada": "L4: HPG-Sec", "nome": "Segurança / Security", "desc": "HSL Auth, Detecção de Intrusão, LFSR Key Rotation", "cor": "#ff4444"},
        {"camada": "L3: HALE", "nome": "Endereçamento / Addressing", "desc": "Pipeline f₀ → H → h → ψ → c → M → g", "cor": "#44ff44"},
        {"camada": "L2: HPG Signal", "nome": "Sinal / Signal", "desc": "Sinal Composto s(t), Decodificação FFT, Verificação Espectral", "cor": "#4488ff"},
        {"camada": "L1: HPG Core", "nome": "Grid", "desc": "H_N, O_N, Totiente de Euler, HPM 1.0", "cor": "#ffaa00"},
    ]

    fig_arch = go.Figure()
    for i, layer in enumerate(layers):
        fig_arch.add_trace(go.Bar(
            y=[layer["camada"]],
            x=[1],
            orientation="h",
            marker_color=layer["cor"],
            text=f"  {layer['nome']}: {layer['desc']}",
            textposition="inside",
            textfont=dict(color="white", size=12),
            showlegend=False,
        ))

    fig_arch.update_layout(
        height=200,
        barmode="stack",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_arch, use_container_width=True)

    st.markdown("---")

    # HPM 1.0 Channel Table
    st.subheader("Tabela de Canais HPM 1.0 / Channel Table")
    st.dataframe(
        table,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "label": st.column_config.TextColumn("Label", width="small"),
            "ratio": st.column_config.TextColumn("Razão a/b"),
            "frequency_hz": st.column_config.NumberColumn("Frequência (Hz)", format="%.1f"),
            "priority": st.column_config.NumberColumn("Prioridade", format="%.4f"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Mathematical formulas
    st.markdown("---")
    st.subheader("Fórmulas Fundamentais / Core Formulas")
    with st.expander("📖 O que essas fórmulas significam? / What do these formulas mean?"):
        st.markdown(
            """
**PT-BR:**
- **H_N:** O conjunto de todas as frequências harmônicas disponíveis.
  Cada fração a/b representa um slot de comunicação único.
- **|H_N|:** Quantidade total de slots (determinada pela função totiente de Euler).
- **O_N:** Espaço de endereços bidimensional — cada slot tem polaridade positiva
  e negativa, dobrando a capacidade.
- **s(t):** O sinal físico real que transmite dados — múltiplos dispositivos
  compartilham o mesmo canal sem interferência.
- **P(a/b):** Prioridade de canal — canais mais "baixos" têm maior prioridade.
- **T_sync:** Período de ressincronização — tempo entre realinhamentos.

**EN:**
- **H_N:** The set of all available harmonic frequencies.
  Each fraction a/b represents a unique communication slot.
- **|H_N|:** Total number of slots (determined by Euler's totient function).
- **O_N:** 2D address space — each slot has positive and negative polarity,
  doubling the capacity.
- **s(t):** The actual physical signal transmitting data — multiple devices
  share the same channel without interference.
- **P(a/b):** Channel priority — lower channels have higher priority.
- **T_sync:** Resynchronization period — time between realignments.
            """
        )

    col1, col2 = st.columns(2)
    with col1:
        st.code("H_N = { a/b ∈ Q⁺ : gcd(a,b)=1, b≤N, a≤N }", language="text")
        st.code("|H_N| = Σ φ(b)  para b=1..N", language="text")
        st.code("O_N = H_N × {-1, +1}", language="text")
    with col2:
        st.code("s(t) = Σ Aₖ sin(2π(aₖ/bₖ)f₀t + φₖ)", language="text")
        st.code("P(a/b) = 1 / (a + b)", language="text")
        st.code("T_sync = lcm(b₁, b₂, ...) / f₀", language="text")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: HALE Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🎵 HALE Pipeline":
    st.header("Pipeline HALE: f₀ → H → h → ψ → c → M → g")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "A Pipeline HALE é o processo de <strong>atribuir automaticamente</strong> "
        "um endereço exclusivo a cada dispositivo IoT conectado. "
        "A frequência mestra (f₀) é dividida matematicamente em subfrequências "
        "harmônicas, cada uma se tornando um canal de comunicação único. "
        "O resultado: cada dispositivo tem seu próprio canal, sem interferência "
        "e sem negociação prévia.<br><br>"
        "The HALE Pipeline is the process of <strong>automatically assigning</strong> "
        "a unique address to every connected IoT device. The master frequency (f₀) "
        "is mathematically divided into harmonic subfrequencies, each becoming a "
        "unique communication channel. Result: every device has its own channel, "
        "no interference, no prior negotiation."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros / Parameters")
        psi_name = st.selectbox(
            "Função ψ",
            ["ψ1: Razão Direta", "ψ2: Totiente", "ψ3: Projeção Trigonométrica", "ψ4: Composta Espectral"],
        )
        psi_map = {
            "ψ1: Razão Direta": psi1,
            "ψ2: Totiente": psi2,
            "ψ3: Projeção Trigonométrica": psi3,
            "ψ4: Composta Espectral": psi4,
        }
        selected_psi = psi_map[psi_name]

        divisors = st.multiselect(
            "Filtrar por divisores b (vazio = todos)",
            options=list(range(1, global_N + 1)),
            default=[],
        )

        run_btn = st.button("▶ Executar Pipeline", type="primary", use_container_width=True)

    if run_btn:
        pipeline = HALEPipeline(
            f0=global_f0,
            max_denominator=global_N,
            psi_function=selected_psi,
        )
        result = pipeline.execute(divisors=divisors if divisors else None)

        with col2:
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("H_N |Canais|", result.grid_size)
            c2.metric("O_N |Endereços|", result.omnigrid_size)
            c3.metric("T_sync (ms)", f"{result.resync_period * 1000:.4f}")
            c4.metric("Cardinalidade", result.cardinality)

            st.caption(
                "Canais = dispositivos que podem comunicar simultaneamente. "
                "Endereços = total de posições únicas na grade. "
                "T_sync = tempo de alinhamento periódico."
            )

            # Pipeline steps visualization
            st.subheader("Etapas do Pipeline / Pipeline Steps")
            steps = [
                ("f₀", f"Frequência Fundamental: {result.f0:,.1f} Hz — o pulso da rede", "#ffaa00"),
                ("H", f"Conjunto H_{global_N}: {result.grid_size} razões racionais únicas — os slots", "#4488ff"),
                ("h", f"Cardinalidade: |H_{global_N}| = {result.cardinality} — total de endereços calculado", "#44ff88"),
                ("ψ", f"Função {psi_name}: mapeamento para endereços numéricos", "#ff44ff"),
                ("c", f"Frequências absolutas: Hz reais de cada canal + prioridades", "#ff8844"),
                ("M", f"Códigos de endereço: hash SHA-256 truncado para identificação", "#88ff44"),
                ("g", f"Grid final: {result.omnigrid_size} endereços bidimensionais prontos", "#00ffff"),
            ]

            for step_id, step_desc, color in steps:
                st.markdown(
                    f"<div style='border-left: 4px solid {color}; "
                    f"padding: 8px 16px; margin: 4px 0; border-radius: 0 8px 8px 0; "
                    f"background: rgba(255,255,255,0.05);'>"
                    f"<strong>{step_id}</strong> → {step_desc}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # Channel grid table
            st.subheader(f"Grid de Canais ({len(result.grid)} canais) / Channel Grid")
            grid_data = [
                {
                    "Razão a/b": str(ch.ratio),
                    "f (Hz)": f"{ch.frequency_hz:,.1f}",
                    "Prioridade": f"{ch.priority:.4f}",
                    "ψ(a/b)": f"{ch.psi_value:.6f}",
                    "Endereço": ch.address_code,
                }
                for ch in result.grid
            ]
            st.dataframe(grid_data, hide_index=True, use_container_width=True)

            # Frequency distribution chart
            if result.grid:
                freqs = [ch.frequency_hz for ch in result.grid]
                ratios = [str(ch.ratio) for ch in result.grid]

                fig = px.bar(
                    x=ratios,
                    y=freqs,
                    title="Distribuição de Frequências por Canal / Frequency Distribution",
                    labels={"x": "Razão a/b", "y": "Frequência (Hz)"},
                )
                fig.update_traces(marker_color="#00ffff")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Omnigrid 2D
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📟 Omnigrid 2D":
    st.header("Omnigrid 2D: O_N = H_N × {-1, +1}")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "O Omnigrid é o espaço de endereços completo do protocolo. "
        "Se H_N tem 80 canais, o Omnigrid tem 160 — cada canal ganha "
        "uma polaridade positiva (+) e uma negativa (-), como os polos "
        "de um imã. Isso dobra a capacidade sem precisar de mais frequências. "
        "Para governos e grandes operações, isso significa o dobro de "
        "dispositivos na mesma infraestrutura.<br><br>"
        "The Omnigrid is the full address space. If H_N has 80 channels, "
        "O_N has 160 — each channel gets a positive (+) and negative (-) "
        "polarity. This doubles capacity without more frequencies. "
        "For governments and large operators: double the devices on "
        "the same infrastructure."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption(f"N = {global_N} | |O_N| = {cardinality_hn(global_N) * 2} endereços / addresses")

    grid = omnigrid_2d(global_N)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Estatísticas / Statistics")
        st.metric("Endereços +1", len([g for g in grid if g["polarity"] == 1]))
        st.caption("Endereços com polaridade positiva")
        st.metric("Endereços -1", len([g for g in grid if g["polarity"] == -1]))
        st.caption("Endereços com polaridade negativa")
        st.metric("Total O_N", len(grid))
        st.caption("Capacidade total de endereçamento")

        st.markdown("---")
        st.subheader("Amostra / Sample")
        sample_size = min(20, len(grid))
        for item in grid[:sample_size]:
            st.code(
                f"{item['address_id']}  f={float(item['ratio'])*global_f0:,.1f} Hz",
                language="text",
            )

    with col2:
        # Scatter plot of the Omnigrid
        x_vals = [float(g["ratio"]) for g in grid]
        y_vals = [g["polarity"] for g in grid]
        colors = ["#00ffff" if p == 1 else "#ff4444" for p in y_vals]
        labels = [g["address_id"] for g in grid]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            marker=dict(
                color=colors,
                size=8,
                opacity=0.8,
            ),
            text=labels,
            textposition="top center",
            textfont=dict(size=7, color="#ffffff"),
            name="Endereços",
        ))

        fig.update_layout(
            title=f"Omnigrid O_{global_N} ({len(grid)} endereços / addresses)",
            xaxis_title="Razão Harmônica a/b",
            yaxis_title="Polaridade",
            yaxis=dict(tickvals=[-1, 1], ticktext=["-1", "+1"]),
            height=500,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Signal + FFT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📡 Sinal Composto + FFT":
    st.header("Sinal Composto s(t) + Decodificação FFT / Composite Signal + FFT")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "Esta seção demonstra a <strong>comunicação real</strong> entre dispositivos. "
        "O gráfico superior mostra o sinal elétrico combinado de múltiplos "
        "dispositivos transmitindo simultaneamente — sem interferência. "
        "O gráfico inferior (FFT) mostra como o sistema <strong>decodifica</strong> "
        "cada dispositivo no sinal combinado. A verificação de integridade "
        "confirma que nenhuma frequência estranha está presente — essencial "
        "para segurança em redes governamentais.<br><br>"
        "This section demonstrates <strong>actual communication</strong> between devices. "
        "The top chart shows the combined electrical signal of multiple devices "
        "transmitting simultaneously — without interference. The bottom chart "
        "(FFT) shows how the system <strong>decodes</strong> each device from the "
        "combined signal. Integrity verification confirms no foreign frequencies "
        "are present — essential for government network security."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros / Parameters")
        duration = st.number_input("Duração (ms)", 1, 100, 10, key="sig_duration")
        sample_rate = st.selectbox("Sample Rate", [44100, 48000, 96000], index=0, key="sig_sr")
        num_channels = st.slider("Número de Canais Harmônicos / Channels", 1, 12, 6, key="sig_ch")

        use_noise = st.checkbox("Adicionar Ruído / Add Noise", value=False, key="sig_noise")
        noise_level = st.slider("Nível de Ruído (%)", 0, 50, 10, key="sig_noise_lvl")

        gen_btn = st.button("📡 Gerar Sinal + FFT / Generate Signal", type="primary", use_container_width=True)

    if gen_btn:
        channel_table = get_channel_table()[:num_channels]
        harmonics = [
            {"a": ch["a"], "b": ch["b"], "amplitude": 1.0, "phase": 0.0}
            for ch in channel_table
        ]

        t, signal, used = generate_composite_signal(
            f0=global_f0,
            harmonics=harmonics,
            duration=duration / 1000.0,
            sample_rate=float(sample_rate),
        )

        if use_noise:
            noise = np.random.normal(0, noise_level / 100.0, len(signal))
            signal = signal + noise

        decoded = decode_fft(signal, sample_rate=float(sample_rate), f0=global_f0)
        report = verify_rational_integrity(decoded, f0=global_f0)

        with col2:
            # Signal waveform
            fig_time = go.Figure()
            fig_time.add_trace(go.Scatter(
                x=t * 1000,
                y=signal,
                mode="lines",
                name="s(t)",
                line=dict(color="#00ffff", width=1),
            ))
            fig_time.update_layout(
                title=f"Sinal Composto ({num_channels} canais / channels)",
                xaxis_title="Tempo (ms)",
                yaxis_title="Amplitude",
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_time, use_container_width=True)

            # FFT spectrum
            fig_fft = go.Figure()
            fig_fft.add_trace(go.Bar(
                x=[d["closest_ratio"] for d in decoded],
                y=[d["amplitude_db"] for d in decoded],
                marker_color="#4488ff",
                name="Magnitude (dB)",
            ))
            fig_fft.update_layout(
                title="Espectro FFT — Componentes Detectados / Detected Components",
                xaxis_title="Razão Harmônica a/b",
                yaxis_title="Amplitude (dB)",
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_fft, use_container_width=True)

            # Spectral integrity
            st.subheader("Verificação de Integridade Espectral / Spectral Integrity")
            c1, c2, c3 = st.columns(3)
            c1.metric("Componentes", report.total_components)
            c2.metric("Válidos", report.valid_components)
            c3.metric("Integridade", f"{report.integrity_score:.1f}%")

            st.caption(
                "100% = todas as frequências detectadas são canais autorizados. "
                "Qualquer valor abaixo de 100% indica possível intrusão ou interferência."
            )

            if report.violations:
                st.warning(f"⚠️ {len(report.violations)} violações detectadas!")
                for v in report.violations:
                    st.code(
                        f"Freq: {v['frequency']:.1f} Hz | "
                        f"Desvio: {v['deviation_hz']:.1f} Hz",
                        language="text",
                    )
            else:
                st.success("✅ Todas as componentes estão dentro do H_N — integridade perfeita. / All components within H_N — perfect integrity.")

            # Detected components table
            if decoded:
                st.subheader("Componentes Decodificados / Decoded Components")
                st.dataframe(decoded, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Security (HSL Auth)
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔐 Segurança (HSL)":
    st.header("Autenticação HSL — Harmonic Signature")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "O HSL é o sistema de autenticação do protocolo Nautam. Funciona em "
        "3 etapas (como um protocolo de mão dupla): o dispositivo se identifica, "
        "o servidor responde com um desafio, e o dispositivo confirma. "
        "O pacote completo tem apenas <strong>~200 bytes</strong> — mais de "
        "100x menor que um pacote TLS padrão. Ideal para sensores IoT com "
        "banda e energia limitadas. Em implantações governamentais, isso "
        "significa autenticação robusta mesmo em dispositivos de baixo custo.<br><br>"
        "HSL is Nautam's authentication. Works in 3 steps (like a handshake): "
        "device identifies, server challenges, device confirms. "
        "The entire packet is only <strong>~200 bytes</strong> — over 100x smaller "
        "than a standard TLS packet. Ideal for low-bandwidth, low-power IoT sensors. "
        "For government deployments: robust authentication even on low-cost devices."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("Protocolo Challenge/Response em 3 etapas (~200 bytes)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Simular Autenticação / Simulate Auth")
        device_id = st.text_input("Device ID", "device-001", key="auth_device")
        auth_btn = st.button("🔐 Executar Challenge/Response", type="primary", use_container_width=True)

        st.markdown("---")
        st.subheader("Protocolo HSL / Protocol Details")
        st.code("""
Etapa 1: CHALLENGE(device_id, timestamp, nonce)
  → SHA-256(device_id:ts:nonce)
  "Quem é você?" — o dispositivo se apresenta

Etapa 2: RESPONSE(challenge_hash, phase_signature)
  → SHA-256(challenge_hash:secret_key)
  "Prove quem é" — o servidor responde com desafio

Etapa 3: CONFIRM(session_key)
  → SHA-256(phase_signature:nonce)
  "Confirmado" — sessão estabelecida
        """, language="text")

    if auth_btn:
        auth = st.session_state.auth_system
        challenge = auth.create_challenge(device_id)
        response = auth.generate_response(challenge)
        verified = auth.verify_response(challenge, response)

        with col2:
            # Step 1
            st.markdown(
                f"<div style='border-left: 4px solid #ffaa00; padding: 8px 16px; margin: 8px 0; "
                f"background: rgba(255,170,0,0.1); border-radius: 0 8px 8px 0;'>"
                f"<strong>Etapa 1 — CHALLENGE (Identificação)</strong><br>"
                f"Device: <code>{challenge.device_id}</code><br>"
                f"Timestamp: <code>{challenge.timestamp:.3f}</code><br>"
                f"Nonce: <code>{challenge.nonce.hex()[:32]}...</code><br>"
                f"Hash: <code>{challenge.challenge_hash[:32]}...</code><br>"
                f"Tamanho: <code>~{challenge.size_bytes} bytes</code></div>",
                unsafe_allow_html=True,
            )

            # Step 2
            st.markdown(
                f"<div style='border-left: 4px solid #4488ff; padding: 8px 16px; margin: 8px 0; "
                f"background: rgba(68,136,255,0.1); border-radius: 0 8px 8px 0;'>"
                f"<strong>Etapa 2 — RESPONSE (Desafio do Servidor)</strong><br>"
                f"Phase Signature: <code>{response.phase_signature[:32]}...</code><br>"
                f"Session Key: <code>{response.session_key[:32]}...</code></div>",
                unsafe_allow_html=True,
            )

            # Step 3
            status_color = "#44ff44" if verified else "#ff4444"
            status_text = "VERIFICADO ✅ / AUTHENTICATED" if verified else "FALHOU ❌ / FAILED"
            st.markdown(
                f"<div style='border-left: 4px solid {status_color}; padding: 8px 16px; margin: 8px 0; "
                f"background: rgba(68,255,68,0.1); border-radius: 0 8px 8px 0;'>"
                f"<strong>Etapa 3 — VERIFICAÇÃO: {status_text}</strong></div>",
                unsafe_allow_html=True,
            )

            if verified:
                st.success("Autenticação bem-sucedida — sessão estabelecida. / Authentication successful — session established.")
            else:
                st.error("Falha na autenticação. / Authentication failed.")

            # Session info
            session_info = auth.get_session_info(response.session_key[:16])
            if session_info:
                st.json(session_info)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Intrusion Detection
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🛡️ Detecção de Intrusão":
    st.header("Detecção de Intrusão — Desvio de Fase / Intrusion Detection")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "Imagine que cada dispositivo IoT transmite com uma \"assinatura\" "
        "de fase — como uma assinatura digital invisível. Se um invasor tentar "
        "se passar por um dispositivo legítimo, a assinatura de fase dele será "
        "diferente. O sistema detecta essa diferença (Δφ > ε) em tempo real "
        "e dispara um alerta. Funciona como um alarme que detecta qualquer "
        "comunicação não autorizada na rede. Essencial para proteger "
        "infraestrutura crítica (energia, água, transporte).<br><br>"
        "Each IoT device transmits with a \"phase signature\" — like an invisible "
        "digital fingerprint. If an intruder tries to impersonate a legitimate "
        "device, their phase signature will differ. The system detects this "
        "difference (Δφ > ε) in real time and triggers an alert. Like an alarm "
        "detecting any unauthorized communication. Essential for critical "
        "infrastructure (energy, water, transport)."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("Regra: Δφ > ε dispara alerta / Rule: Δφ > ε triggers alert")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros / Parameters")
        threshold_deg = st.slider("Limiar ε (graus / degrees)", 0.5, 30.0, 5.0, step=0.5, key="intr_thresh")
        threshold_rad = threshold_deg * 3.14159 / 180.0

        inject_intrusion = st.checkbox("Injetar intrusão / Inject intrusion", value=True, key="intr_inject")
        deviation_deg = st.slider("Desvio do intruso (graus / degrees)", 5, 45, 15, key="intr_dev")

        detect_btn = st.button("🔍 Executar Detecção / Run Detection", type="primary", use_container_width=True)

    if detect_btn:
        channel_table = get_channel_table()
        detector = IntrusionDetector(threshold_rad=threshold_rad)

        for ch in channel_table[:8]:
            detector.register_channel(ch["label"], expected_phase=0.0)

        # Generate observed phases (with optional intrusion)
        observed = {}
        for ch in channel_table[:8]:
            if inject_intrusion and ch["id"] == 3:
                observed[ch["label"]] = deviation_deg * 3.14159 / 180.0
            else:
                observed[ch["label"]] = np.random.uniform(-0.02, 0.02)

        report = detector.check_phases(observed)

        with col2:
            # Alert summary
            severity_colors = {
                "none": "#44ff44",
                "low": "#88ff44",
                "medium": "#ffaa00",
                "high": "#ff8844",
                "critical": "#ff4444",
            }
            sev_color = severity_colors.get(report.severity, "#888")

            st.markdown(
                f"<div style='border: 2px solid {sev_color}; padding: 16px; border-radius: 12px; "
                f"background: rgba(0,0,0,0.3); text-align: center; color: #ffffff;'>"
                f"<div style='font-size: 2rem; color: {sev_color}; font-weight: bold;'>"
                f"{report.severity.upper()}</div>"
                f"<div style='color: #ffffff;'>Canais monitorados: {report.total_channels} | "
                f"Alertas: {report.alert_channels}</div></div>",
                unsafe_allow_html=True,
            )

            st.caption(
                "NONE = sem intrusão. MEDIUM/HIGH = desvio suspeito. "
                "CRITICAL = múltiplos canais comprometidos."
            )

            # Per-channel deviation chart
            if report.alerts or observed:
                channels_list = list(observed.keys())
                deviations = [observed.get(ch, 0) * 180 / 3.14159 for ch in channels_list]
                threshold_line = [threshold_deg] * len(channels_list)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=channels_list,
                    y=deviations,
                    name="Desvio Δφ",
                    marker_color=["#ff4444" if abs(d) > threshold_deg else "#4488ff" for d in deviations],
                ))
                fig.add_hline(
                    y=threshold_deg,
                    line_dash="dash",
                    line_color="#ffaa00",
                    annotation_text=f"Limiar ε = {threshold_deg}°",
                )
                fig.update_layout(
                    title="Desvio de Fase por Canal / Phase Deviation per Channel",
                    xaxis_title="Canal",
                    yaxis_title="Desvio (graus / degrees)",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Alert details
            if report.alerts:
                st.warning(f"⚠️ {len(report.alerts)} alerta(s) de intrusão detectado(s)! / intrusion alert(s) detected!")
                for alert in report.alerts:
                    st.error(
                        f"🚨 {alert['channel_id']}: "
                        f"Δφ = {alert['deviation_deg']:.2f}° "
                        f"(limiar: {threshold_deg}° / threshold: {threshold_deg}°)"
                    )
            else:
                st.success("✅ Todos os canais dentro do limiar — sem intrusão detectada. / All channels within threshold — no intrusion detected.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: LFSR Key Rotation
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔑 Rotação de Chaves (LFSR)":
    st.header("Rotação de Chaves — LFSR / Key Rotation")

    st.markdown(
        "<div class='exec-box'>"
        "<strong>Em termos simples / In simple terms:</strong><br>"
        "Assim como uma senha deve ser trocada periodicamente, as chaves "
        "criptográficas do protocolo Nautam também são rotacionadas automaticamente. "
        "O LFSR (Registrador de Deslocamento com Feedback Linear) gera uma "
        "sequência de chaves a partir de uma semente — cada chave é única e "
        "imprevisível. Um registrador de 16 bits gera 65.535 chaves antes de "
        "se repetir; 32 bits gera mais de 4 bilhões. Para redes governamentais, "
        "isso garante que mesmo se uma chave for comprometida, as próximas "
        "comunicações estarão protegidas por chaves diferentes.<br><br>"
        "Just like passwords must be changed periodically, Nautam's cryptographic "
        "keys are automatically rotated. The LFSR generates a unique, unpredictable "
        "key sequence from a seed. A 16-bit register generates 65,535 keys before "
        "repeating; 32 bits generates over 4 billion. For government networks, "
        "even if one key is compromised, subsequent communications are protected "
        "by different keys."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("Linear Feedback Shift Register para rotação periódica de chaves / Periodic key rotation")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros / Parameters")
        reg_size = st.selectbox("Tamanho do Registrador (bits) / Register Size", [8, 16, 32], index=1, key="lfsr_size")
        seed = st.number_input("Seed", 0, 2**32 - 1, 0xDEADBEEF, key="lfsr_seed")
        num_keys = st.slider("Número de Chaves a Gerar / Keys to Generate", 1, 20, 10, key="lfsr_count")

        gen_btn = st.button("🔑 Gerar Chaves / Generate Keys", type="primary", use_container_width=True)
        reset_btn = st.button("🔄 Resetar LFSR / Reset")

    if reset_btn:
        st.session_state.key_rotation = LFSRKeyRotation(seed=seed, register_size=reg_size)
        st.rerun()

    if gen_btn:
        lfsr = LFSRKeyRotation(seed=seed, register_size=reg_size)
        keys = lfsr.next_keys(num_keys)

        with col2:
            st.subheader(f"Chaves Geradas ({num_keys}) / Generated Keys")
            st.metric("Período Máximo / Max Period", f"2^{reg_size} - 1 = {lfsr.period:,}")

            st.caption(
                "Número de chaves únicas antes de a sequência se repetir. "
                "Chaves maiores = mais segurança."
            )

            for i, key in enumerate(keys):
                st.code(
                    f"Key {i+1:02d}: {key[:32]}...{key[32:]}",
                    language="text",
                )

            st.markdown("---")
            st.subheader("Distribuição dos Bytes / Byte Distribution")
            # Visualize first byte distribution
            byte_vals = [int(k[:2], 16) for k in keys]
            fig = px.histogram(
                x=byte_vals,
                nbins=32,
                title="Distribuição do 1º Byte das Chaves / 1st Byte Distribution",
                labels={"x": "Valor do Byte", "y": "Frequência"},
            )
            fig.update_traces(marker_color="#00ffff")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

# ─── Footer ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.85rem;'>"
    "<strong>Nautam</strong> by <strong>Hubstry Deep Tech</strong> | "
    "Fundada em 2023 | Brasil<br>"
    "Autor: Guilherme Gonçalves Machado | "
    "ORCID: 0009-0008-1083-0784<br>"
    "DOI: <a href='https://doi.org/10.5281/zenodo.18901934'>10.5281/zenodo.18901934</a> | "
    "DOI: <a href='https://doi.org/10.5281/zenodo.19056387'>10.5281/zenodo.19056387</a>"
    "</div>",
    unsafe_allow_html=True,
)
