"""Nautam IoT Protocol — Interactive Dashboard.

Streamlit dashboard that executes the real HALE + HPG pipeline
and visualizes harmonic protocol operations.

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
    st.markdown("### Navegação")
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
    st.markdown("### Parâmetros Globais")
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
    st.markdown(
        "<small style='color: #666;'>"
        "DOI: [10.5281/zenodo.18901934](https://doi.org/10.5281/zenodo.18901934) | "
        "DOI: [10.5281/zenodo.19056387](https://doi.org/10.5281/zenodo.19056387)"
        "</small>",
        unsafe_allow_html=True,
    )

# ─── Main Content ─────────────────────────────────────────────────────────────

st.title("🌊 Nautam IoT Protocol — Dashboard")
st.caption("HALE + HPG Framework | Pipeline real em Python")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 0: Overview
# ═══════════════════════════════════════════════════════════════════════════════

if page == "📊 Visão Geral":
    st.header("Visão Geral do Protocolo")

    # Quick metrics
    col1, col2, col3, col4 = st.columns(4)
    cardinality = cardinality_hn(global_N)
    table = get_channel_table()
    t_sync = global_f0 / cardinality if cardinality > 0 else 0

    with col1:
        st.metric("Canais H_N", cardinality)
    with col2:
        st.metric("Endereços O_N", cardinality * 2)
    with col3:
        st.metric("Canais HPM 1.0", len(table))
    with col4:
        st.metric("f₀ (Hz)", f"{global_f0:,.0f}")

    st.markdown("---")

    # Architecture diagram
    st.subheader("Arquitetura — 4 Camadas")

    layers = [
        {"camada": "L4: HPG-Sec", "nome": "Segurança", "desc": "HSL Auth, Detecção de Intrusão, LFSR Key Rotation", "cor": "#ff4444"},
        {"camada": "L3: HALE", "nome": "Endereçamento", "desc": "Pipeline f₀ → H → h → ψ → c → M → g", "cor": "#44ff44"},
        {"camada": "L2: HPG Signal", "nome": "Sinal", "desc": "Sinal Composto s(t), Decodificação FFT, Verificação Espectral", "cor": "#4488ff"},
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
    st.subheader("Tabela de Canais HPM 1.0")
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
    st.subheader("Fórmulas Fundamentais")
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

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros")
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

            # Pipeline steps visualization
            st.subheader("Etapas do Pipeline")
            steps = [
                ("f₀", f"Frequência Fundamental: {result.f0:,.1f} Hz", "#ffaa00"),
                ("H", f"Conjunto H_{global_N}: {result.grid_size} razões racionais únicas", "#4488ff"),
                ("h", f"Cardinalidade: |H_{global_N}| = {result.cardinality}", "#44ff88"),
                ("ψ", f"Função {psi_name}: mapeamento para endereços", "#ff44ff"),
                ("c", f"Frequências absolutas + prioridades", "#ff8844"),
                ("M", f"Códigos de endereço (SHA-256 truncado)", "#88ff44"),
                ("g", f"Grid final: {result.omnigrid_size} endereços bidimensionais", "#00ffff"),
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
            st.subheader(f"Grid de Canais ({len(result.grid)} canais)")
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
                    title="Distribuição de Frequências por Canal",
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

    st.caption(f"N = {global_N} | |O_N| = {cardinality_hn(global_N) * 2} endereços")

    grid = omnigrid_2d(global_N)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Estatísticas")
        st.metric("Endereços +1", len([g for g in grid if g["polarity"] == 1]))
        st.metric("Endereços -1", len([g for g in grid if g["polarity"] == -1]))
        st.metric("Total O_N", len(grid))

        st.markdown("---")
        st.subheader("Amostra")
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
            textfont=dict(size=7, color="#aaaaaa"),
            name="Endereços",
        ))

        fig.update_layout(
            title=f"Omnigrid O_{global_N} ({len(grid)} endereços)",
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
    st.header("Sinal Composto s(t) + Decodificação FFT")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros do Sinal")
        duration = st.number_input("Duração (ms)", 1, 100, 10, key="sig_duration")
        sample_rate = st.selectbox("Sample Rate", [44100, 48000, 96000], index=0, key="sig_sr")
        num_channels = st.slider("Número de Canais Harmônicos", 1, 12, 6, key="sig_ch")

        use_noise = st.checkbox("Adicionar Ruído", value=False, key="sig_noise")
        noise_level = st.slider("Nível de Ruído (%)", 0, 50, 10, key="sig_noise_lvl")

        gen_btn = st.button("📡 Gerar Sinal + FFT", type="primary", use_container_width=True)

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
                title=f"Sinal Composto ({num_channels} canais harmônicos)",
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
                title="Espectro FFT — Componentes Detectados",
                xaxis_title="Razão Harmônica a/b",
                yaxis_title="Amplitude (dB)",
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_fft, use_container_width=True)

            # Spectral integrity
            st.subheader("Verificação de Integridade Espectral")
            c1, c2, c3 = st.columns(3)
            c1.metric("Componentes", report.total_components)
            c2.metric("Válidos", report.valid_components)
            c3.metric("Integridade", f"{report.integrity_score:.1f}%")

            if report.violations:
                st.warning(f"⚠️ {len(report.violations)} violações detectadas!")
                for v in report.violations:
                    st.code(
                        f"Freq: {v['frequency']:.1f} Hz | "
                        f"Desvio: {v['deviation_hz']:.1f} Hz",
                        language="text",
                    )
            else:
                st.success("✅ Todas as componentes estão dentro do H_N — integridade perfeita.")

            # Detected components table
            if decoded:
                st.subheader("Componentes Decodificados")
                st.dataframe(decoded, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Security (HSL Auth)
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔐 Segurança (HSL)":
    st.header("Autenticação HSL — Harmonic Signature")

    st.caption("Protocolo Challenge/Response em 3 etapas (~200 bytes)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Simular Autenticação")
        device_id = st.text_input("Device ID", "device-001", key="auth_device")
        auth_btn = st.button("🔐 Executar Challenge/Response", type="primary", use_container_width=True)

        st.markdown("---")
        st.subheader("Protocolo HSL")
        st.code("""
Etapa 1: CHALLENGE(device_id, timestamp, nonce)
  → SHA-256(device_id:ts:nonce)

Etapa 2: RESPONSE(challenge_hash, phase_signature)
  → SHA-256(challenge_hash:secret_key)

Etapa 3: CONFIRM(session_key)
  → SHA-256(phase_signature:nonce)
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
                f"<strong>Etapa 1 — CHALLENGE</strong><br>"
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
                f"<strong>Etapa 2 — RESPONSE</strong><br>"
                f"Phase Signature: <code>{response.phase_signature[:32]}...</code><br>"
                f"Session Key: <code>{response.session_key[:32]}...</code></div>",
                unsafe_allow_html=True,
            )

            # Step 3
            status_color = "#44ff44" if verified else "#ff4444"
            status_text = "VERIFICADO ✅" if verified else "FALHOU ❌"
            st.markdown(
                f"<div style='border-left: 4px solid {status_color}; padding: 8px 16px; margin: 8px 0; "
                f"background: rgba(68,255,68,0.1); border-radius: 0 8px 8px 0;'>"
                f"<strong>Etapa 3 — VERIFICAÇÃO: {status_text}</strong></div>",
                unsafe_allow_html=True,
            )

            if verified:
                st.success("Autenticação bem-sucedida — sessão estabelecida.")
            else:
                st.error("Falha na autenticação.")

            # Session info
            session_info = auth.get_session_info(response.session_key[:16])
            if session_info:
                st.json(session_info)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Intrusion Detection
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🛡️ Detecção de Intrusão":
    st.header("Detecção de Intrusão — Desvio de Fase")

    st.caption("Regra: Δφ > ε dispara alerta")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros")
        threshold_deg = st.slider("Limiar ε (graus)", 0.5, 30.0, 5.0, step=0.5, key="intr_thresh")
        threshold_rad = threshold_deg * 3.14159 / 180.0

        inject_intrusion = st.checkbox("Injetar intrusão (desvio alto)", value=True, key="intr_inject")
        deviation_deg = st.slider("Desvio do intruso (graus)", 5, 45, 15, key="intr_dev")

        detect_btn = st.button("🔍 Executar Detecção", type="primary", use_container_width=True)

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
                f"background: rgba(0,0,0,0.3); text-align: center;'>"
                f"<div style='font-size: 2rem; color: {sev_color}; font-weight: bold;'>"
                f"{report.severity.upper()}</div>"
                f"<div>Canais monitorados: {report.total_channels} | "
                f"Alertas: {report.alert_channels}</div></div>",
                unsafe_allow_html=True,
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
                    title="Desvio de Fase por Canal",
                    xaxis_title="Canal",
                    yaxis_title="Desvio (graus)",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Alert details
            if report.alerts:
                st.warning(f"⚠️ {len(report.alerts)} alerta(s) de intrusão detectado(s)!")
                for alert in report.alerts:
                    st.error(
                        f"🚨 {alert['channel_id']}: "
                        f"Δφ = {alert['deviation_deg']:.2f}° "
                        f"(limiar: {threshold_deg}°)"
                    )
            else:
                st.success("✅ Todos os canais dentro do limiar — sem intrusão detectada.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: LFSR Key Rotation
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔑 Rotação de Chaves (LFSR)":
    st.header("Rotação de Chaves — LFSR")

    st.caption("Linear Feedback Shift Register para rotação periódica de chaves")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parâmetros")
        reg_size = st.selectbox("Tamanho do Registrador (bits)", [8, 16, 32], index=1, key="lfsr_size")
        seed = st.number_input("Seed", 0, 2**32 - 1, 0xDEADBEEF, key="lfsr_seed")
        num_keys = st.slider("Número de Chaves a Gerar", 1, 20, 10, key="lfsr_count")

        gen_btn = st.button("🔑 Gerar Chaves", type="primary", use_container_width=True)
        reset_btn = st.button("🔄 Resetar LFSR")

    if reset_btn:
        st.session_state.key_rotation = LFSRKeyRotation(seed=seed, register_size=reg_size)
        st.rerun()

    if gen_btn:
        lfsr = LFSRKeyRotation(seed=seed, register_size=reg_size)
        keys = lfsr.next_keys(num_keys)

        with col2:
            st.subheader(f"Chaves Geradas ({num_keys})")
            st.metric("Período Máximo", f"2^{reg_size} - 1 = {lfsr.period:,}")

            for i, key in enumerate(keys):
                st.code(
                    f"Key {i+1:02d}: {key[:32]}...{key[32:]}",
                    language="text",
                )

            st.markdown("---")
            st.subheader("Distribuição dos Bytes")
            # Visualize first byte distribution
            byte_vals = [int(k[:2], 16) for k in keys]
            fig = px.histogram(
                x=byte_vals,
                nbins=32,
                title="Distribuição do 1º Byte das Chaves",
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
