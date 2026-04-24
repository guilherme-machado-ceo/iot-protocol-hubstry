"""Composite Signal Generation and FFT Decoding.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

Composite Signal:
    s(t) = sum_{k=1}^{K} A_k * sin(2*pi*(a_k/b_k)*f0*t + phi_k)

Where:
    K = number of active channels
    A_k = amplitude of channel k
    a_k/b_k = rational harmonic ratio of channel k
    f0 = fundamental frequency (Hz)
    phi_k = initial phase of channel k (radians)

FFT Decoding:
    Apply Fast Fourier Transform to the sampled signal to decompose
    it into individual harmonic components, extracting (frequency,
    amplitude, phase) for each detected peak.

Dependencies:
    numpy (for FFT): pip install numpy
    All other code uses Python standard library only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class HarmonicComponent:
    """A single harmonic component in the composite signal.

    Attributes:
        a: Numerator of the harmonic ratio.
        b: Denominator of the harmonic ratio.
        amplitude: Peak amplitude A_k.
        phase: Initial phase phi_k in radians.
    """

    a: int
    b: int
    amplitude: float = 1.0
    phase: float = 0.0

    @property
    def ratio(self) -> float:
        """Rational harmonic ratio a/b."""
        return self.a / self.b

    @property
    def frequency(self, f0: float) -> float:  # type: ignore[override]
        """Compute frequency at a given f0."""
        return self.ratio * f0


def generate_composite_signal(
    t: List[float],
    components: List[HarmonicComponent],
    f0: float,
) -> List[float]:
    """Generate the composite harmonic signal s(t).

    s(t) = sum_{k=1}^{K} A_k * sin(2*pi*(a_k/b_k)*f0*t + phi_k)

    Args:
        t: List of time points in seconds.
        components: List of HarmonicComponent objects defining active channels.
        f0: Fundamental frequency in Hz.

    Returns:
        List of signal values s(t) at each time point.
    """
    signal = [0.0] * len(t)
    two_pi = 2.0 * math.pi

    for comp in components:
        freq = comp.ratio * f0
        angular_freq = two_pi * freq
        for i, ti in enumerate(t):
            signal[i] += comp.amplitude * math.sin(angular_freq * ti + comp.phase)

    return signal


def generate_signal_numpy(
    t: np.ndarray,
    components: List[HarmonicComponent],
    f0: float,
) -> np.ndarray:
    """Generate composite signal using numpy for performance.

    Args:
        t: Numpy array of time points in seconds.
        components: List of HarmonicComponent objects.
        f0: Fundamental frequency in Hz.

    Returns:
        Numpy array of signal values.
    """
    if not HAS_NUMPY:
        raise ImportError("numpy is required for generate_signal_numpy")
    signal = np.zeros_like(t)
    two_pi = 2.0 * np.pi
    for comp in components:
        freq = comp.ratio * f0
        signal += comp.amplitude * np.sin(two_pi * freq * t + comp.phase)
    return signal


@dataclass
class FFTResult:
    """Result of FFT decoding of a composite signal.

    Attributes:
        frequencies: Detected frequencies in Hz.
        amplitudes: Detected amplitudes.
        phases: Detected phases in radians.
        sample_rate: Sampling rate used.
        num_samples: Number of samples analyzed.
    """

    frequencies: List[float]
    amplitudes: List[float]
    phases: List[float]
    sample_rate: float
    num_samples: int

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries."""
        results = []
        for i in range(len(self.frequencies)):
            results.append({
                "index": i,
                "frequency_hz": self.frequencies[i],
                "amplitude": self.amplitudes[i],
                "phase_rad": self.phases[i],
                "phase_deg": math.degrees(self.phases[i]),
            })
        return results


def decode_fft(
    signal: List[float],
    sample_rate: float,
    f0: float,
    min_amplitude: float = 0.01,
) -> FFTResult:
    """Decode a composite signal using FFT.

    Applies the Fast Fourier Transform to decompose the signal
    into individual frequency components. Peaks above min_amplitude
    are extracted with their frequencies, amplitudes, and phases.

    Args:
        signal: List of signal samples.
        sample_rate: Sampling rate in Hz.
        f0: Fundamental frequency (used for frequency resolution).
        min_amplitude: Minimum amplitude threshold for peak detection.

    Returns:
        FFTResult with detected harmonic components.

    Raises:
        ImportError: If numpy is not available.
    """
    if not HAS_NUMPY:
        raise ImportError("numpy is required for FFT decoding")

    n = len(signal)
    x = np.array(signal)

    fft_vals = np.fft.rfft(x)
    magnitudes = np.abs(fft_vals) / n
    magnitudes[1:] *= 2.0
    phases = np.angle(fft_vals)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

    peak_indices = []
    for i in range(1, len(magnitudes)):
        if magnitudes[i] > min_amplitude:
            if i == 1 or magnitudes[i] >= magnitudes[i - 1]:
                if i == len(magnitudes) - 1 or magnitudes[i] >= magnitudes[i + 1]:
                    peak_indices.append(i)

    frequencies: List[float] = []
    amplitudes: List[float] = []
    phases_list: List[float] = []

    for idx in peak_indices:
        frequencies.append(float(freqs[idx]))
        amplitudes.append(float(magnitudes[idx]))
        phases_list.append(float(phases[idx]))

    return FFTResult(
        frequencies=frequencies,
        amplitudes=amplitudes,
        phases=phases_list,
        sample_rate=sample_rate,
        num_samples=n,
    )


def create_time_vector(duration: float, sample_rate: float) -> List[float]:
    """Create a time vector for signal generation.

    Args:
        duration: Signal duration in seconds.
        sample_rate: Samples per second.

    Returns:
        List of time points.
    """
    n_samples = int(duration * sample_rate)
    dt = 1.0 / sample_rate
    return [i * dt for i in range(n_samples)]


if __name__ == "__main__":
    print("=" * 60)
    print("Signal Processing - Example Usage")
    print("=" * 60)

    f0 = 16384.0
    sample_rate = 100000.0
    duration = 0.01

    components = [
        HarmonicComponent(a=1, b=1, amplitude=1.0, phase=0.0),
        HarmonicComponent(a=1, b=2, amplitude=0.5, phase=0.0),
        HarmonicComponent(a=2, b=3, amplitude=0.3, phase=math.pi / 4),
        HarmonicComponent(a=3, b=4, amplitude=0.2, phase=0.0),
    ]

    print(f"\nf0 = {f0} Hz")
    print(f"Sample rate = {sample_rate} Hz")
    print(f"Duration = {duration} s")
    print(f"\nActive channels:")
    for comp in components:
        freq = comp.ratio * f0
        print(f"  {comp.a}/{comp.b}: {freq:.1f} Hz, "
              f"A={comp.amplitude}, phi={comp.phase:.4f} rad")

    t = create_time_vector(duration, sample_rate)
    print(f"\nTime vector: {len(t)} samples")

    signal = generate_composite_signal(t, components, f0)
    print(f"Signal generated: {len(signal)} samples")
    print(f"  Min value: {min(signal):.6f}")
    print(f"  Max value: {max(signal):.6f}")

    if HAS_NUMPY:
        print("\n--- FFT Decoding ---")
        result = decode_fft(signal, sample_rate, f0, min_amplitude=0.05)
        print(f"Detected {len(result.frequencies)} peaks:")
        for peak in result.to_dict():
            print(
                f"  [{peak['index']}] {peak['frequency_hz']:10.2f} Hz, "
                f"A={peak['amplitude']:.4f}, "
                f"phi={peak['phase_deg']:.1f} deg"
            )
    else:
        print("\nnumpy not available - FFT decoding skipped")
        print("Install with: pip install numpy")