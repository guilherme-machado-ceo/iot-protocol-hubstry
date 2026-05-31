"""Signal processing: composite signal generation and FFT decoding.

s(t) = Σ Aₖ sin(2π(aₖ/bₖ)f₀t + φₖ)

The composite signal superposes harmonic components onto a single
carrier waveform. Each device transmits on its assigned harmonic
ratio, enabling simultaneous multi-device communication via
frequency-division multiplexing.

Reference: DOI 10.5281/zenodo.19056387 (CC BY 4.0)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


def generate_composite_signal(
    f0: float = 16384.0,
    harmonics: Optional[List[Dict]] = None,
    duration: float = 0.01,
    sample_rate: float = 44100.0,
) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """Generate a composite harmonic signal s(t).

    s(t) = Σ Aₖ sin(2π(aₖ/bₖ)f₀t + φₖ)

    Args:
        f0: Fundamental frequency in Hz (default: 16384).
        harmonics: List of dicts with keys: a, b, amplitude (optional),
                   phase (optional). If None, uses HPM 1.0 defaults.
        duration: Signal duration in seconds (default: 0.01 = 10ms).
        sample_rate: Sampling rate in Hz (default: 44100).

    Returns:
        Tuple of (time_array, signal_array, harmonics_used).
    """
    from .hpm_config import get_channel_table

    if harmonics is None:
        channel_table = get_channel_table()
        harmonics = [
            {"a": ch["a"], "b": ch["b"], "amplitude": 1.0, "phase": 0.0}
            for ch in channel_table[:6]  # Use first 6 channels
        ]

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = np.zeros_like(t)

    for h in harmonics:
        a = h["a"]
        b = h["b"]
        amp = h.get("amplitude", 1.0)
        phase = h.get("phase", 0.0)
        freq = (a / b) * f0
        signal += amp * np.sin(2 * np.pi * freq * t + phase)

    return t, signal, harmonics


def decode_fft(
    signal: np.ndarray,
    sample_rate: float = 44100.0,
    f0: float = 16384.0,
    threshold_db: float = -40.0,
) -> List[Dict]:
    """Decode a composite signal using FFT to identify active harmonic channels.

    Performs spectral analysis and returns detected harmonic components
    with their frequencies, amplitudes, and closest H_N ratios.

    Args:
        signal: Time-domain signal array.
        sample_rate: Sampling rate in Hz (default: 44100).
        f0: Fundamental frequency for harmonic identification (default: 16384).
        threshold_db: Minimum amplitude in dB to consider a peak (default: -40).

    Returns:
        List of dicts with keys: frequency, amplitude_db, ratio_a, ratio_b,
        closest_ratio, deviation_hz.
    """
    n = len(signal)
    fft_result = np.fft.rfft(signal)
    magnitudes = np.abs(fft_result)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

    # Normalize to dB
    max_mag = np.max(magnitudes)
    if max_mag > 0:
        magnitudes_db = 20 * np.log10(magnitudes / max_mag + 1e-12)
    else:
        magnitudes_db = np.full_like(magnitudes, -np.inf)

    # Find peaks above threshold
    peaks = []
    for i in range(1, len(magnitudes) - 1):
        if (
            magnitudes_db[i] > threshold_db
            and magnitudes_db[i] > magnitudes_db[i - 1]
            and magnitudes_db[i] > magnitudes_db[i + 1]
        ):
            peaks.append({
                "index": i,
                "frequency": freqs[i],
                "amplitude_db": float(magnitudes_db[i]),
            })

    # Identify closest harmonic ratios
    detected = []
    for peak in peaks:
        freq = peak["frequency"]
        ratio = freq / f0 if f0 > 0 else 0

        # Find closest a/b with small denominators
        best_a, best_b, best_dev = 1, 1, abs(ratio - 1)
        for b in range(1, 33):
            a = round(ratio * b)
            if a > 0 and a <= 100:
                dev = abs(ratio - a / b)
                if dev < best_dev:
                    best_a, best_b, best_dev = a, b, dev

        detected.append({
            "frequency": float(freq),
            "amplitude_db": float(peak["amplitude_db"]),
            "ratio_a": best_a,
            "ratio_b": best_b,
            "closest_ratio": f"{best_a}/{best_b}",
            "deviation_hz": float(best_dev * f0),
        })

    # Sort by amplitude (strongest first)
    detected.sort(key=lambda x: x["amplitude_db"], reverse=True)
    return detected


__all__ = ["generate_composite_signal", "decode_fft"]
