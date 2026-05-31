"""Spectral verification: rational ratio integrity.

Verifies that detected frequency components in a signal correspond
to valid rational harmonic ratios from the H_N set. This ensures
no unauthorized or corrupted channels are present.

Reference: DOI 10.5281/zenodo.19056387 (CC BY 4.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd, isclose
from typing import Dict, List, Optional, Tuple


@dataclass
class SpectralReport:
    """Result of spectral integrity verification.

    Attributes:
        total_components: Number of frequency components analyzed.
        valid_components: Number matching valid H_N ratios.
        invalid_components: Number not matching H_N.
        integrity_score: Percentage of valid components (0-100).
        violations: List of invalid component details.
        passed: Whether integrity meets threshold (default: 100%).
    """

    total_components: int = 0
    valid_components: int = 0
    invalid_components: int = 0
    integrity_score: float = 0.0
    violations: List[Dict] = field(default_factory=list)
    threshold: float = 100.0

    @property
    def passed(self) -> bool:
        return self.integrity_score >= self.threshold


def verify_rational_integrity(
    detected_components: List[Dict],
    f0: float = 16384.0,
    max_denominator: int = 32,
    tolerance_hz: float = 50.0,
    threshold: float = 100.0,
) -> SpectralReport:
    """Verify that detected frequency components are valid harmonic ratios.

    Checks each detected frequency against the H_N set.
    A component is valid if freq/f0 ≈ a/b for some a/b in H_N
    within the specified tolerance.

    Args:
        detected_components: List of dicts with 'frequency' key (Hz).
            Optionally 'ratio_a' and 'ratio_b' from FFT decoder.
        f0: Fundamental frequency (default: 16384).
        max_denominator: Maximum denominator N for H_N (default: 32).
        tolerance_hz: Maximum frequency deviation for a match (default: 50 Hz).
        threshold: Minimum integrity score to pass (default: 100.0).

    Returns:
        SpectralReport with verification results.
    """
    # Build reference set of valid frequencies
    valid_ratios = set()
    for b in range(1, max_denominator + 1):
        for a in range(1, max_denominator + 1):
            if gcd(a, b) == 1:
                valid_ratios.add((a, b))

    valid_freqs = {(a / b) * f0 for a, b in valid_ratios}

    report = SpectralReport(threshold=threshold)
    report.total_components = len(detected_components)

    for comp in detected_components:
        freq = comp["frequency"]

        # Check if frequency matches any valid harmonic
        matched = False
        for valid_f in valid_freqs:
            if isclose(freq, valid_f, abs_tol=tolerance_hz):
                matched = True
                break

        if matched:
            report.valid_components += 1
        else:
            report.invalid_components += 1
            report.violations.append({
                "frequency": freq,
                "ratio": freq / f0 if f0 > 0 else 0,
                "deviation_hz": _min_deviation(freq, valid_freqs),
            })

    if report.total_components > 0:
        report.integrity_score = (
            (report.valid_components / report.total_components) * 100
        )

    return report


def _min_deviation(freq: float, valid_freqs: set) -> float:
    """Find the minimum frequency deviation from any valid harmonic."""
    if not valid_freqs:
        return float("inf")
    return min(abs(freq - vf) for vf in valid_freqs)


__all__ = ["verify_rational_integrity", "SpectralReport"]
