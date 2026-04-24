"""Spectral Verification - Rational Ratio Integrity.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

This module provides verification utilities to ensure that detected
frequencies in a composite signal correspond to valid rational harmonic
ratios from the HPG grid.

Key verification:
    Given a detected frequency f and fundamental f0, verify that
    f/f0 = a/b where gcd(a,b) = 1 and a,b <= N.

This is essential for:
    - Validating that received signals originate from HPG-compliant devices
    - Detecting spoofed or corrupted signals with non-harmonic frequencies
    - Ensuring spectral integrity of the communication channel
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class VerificationResult:
    """Result of rational ratio verification.

    Attributes:
        frequency: The frequency being verified (Hz).
        f0: The fundamental frequency used (Hz).
        is_valid: Whether the frequency is a valid harmonic ratio.
        ratio: The detected rational ratio a/b (as Fraction).
        a: Numerator.
        b: Denominator.
        gcd_value: gcd(a, b) - should be 1 for reduced form.
        error: Relative error between f/f0 and a/b.
        max_denominator: The N value used for H_N membership check.
        in_grid: Whether the ratio is in H_N (b <= N and a <= N).
    """

    frequency: float
    f0: float
    is_valid: bool = False
    ratio: Optional[Fraction] = None
    a: int = 0
    b: int = 0
    gcd_value: int = 0
    error: float = float("inf")
    max_denominator: int = 16
    in_grid: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frequency_hz": self.frequency,
            "f0_hz": self.f0,
            "is_valid": self.is_valid,
            "ratio": str(self.ratio) if self.ratio else None,
            "a": self.a,
            "b": self.b,
            "gcd": self.gcd_value,
            "relative_error": self.error,
            "max_denominator": self.max_denominator,
            "in_grid": self.in_grid,
        }


def verify_rational_ratio(
    frequency: float,
    f0: float,
    tolerance: float = 1e-4,
    max_denominator: int = 16,
    max_numerator: int = 16,
) -> VerificationResult:
    """Verify that a frequency is a valid rational harmonic of f0.

    Checks whether frequency / f0 can be expressed as a/b where:
        1. gcd(a, b) = 1 (reduced form)
        2. b <= max_denominator
        3. a <= max_numerator
        4. |frequency/f0 - a/b| <= tolerance

    Algorithm:
        1. Compute the raw ratio: r = frequency / f0
        2. Approximate r as a fraction with bounded denominator
        3. Check coprimality and grid membership

    Args:
        frequency: Frequency to verify (Hz).
        f0: Fundamental frequency (Hz).
        tolerance: Maximum relative error for ratio matching.
        max_denominator: Maximum allowed denominator N.
        max_numerator: Maximum allowed numerator.

    Returns:
        VerificationResult with detailed analysis.
    """
    if f0 <= 0:
        return VerificationResult(frequency=frequency, f0=f0)

    raw_ratio = frequency / f0
    fraction = Fraction(raw_ratio).limit_denominator(max_denominator * max_numerator)
    a = fraction.numerator
    b = fraction.denominator

    g = math.gcd(a, b)
    reduced_a = a // g
    reduced_b = b // g
    reduced_fraction = Fraction(reduced_a, reduced_b)

    relative_error = abs(raw_ratio - float(reduced_fraction)) / float(reduced_fraction)

    is_valid = (
        relative_error <= tolerance
        and reduced_b <= max_denominator
        and reduced_a <= max_numerator
        and g == 1
    )

    in_grid = reduced_b <= max_denominator and reduced_a <= max_numerator

    return VerificationResult(
        frequency=frequency,
        f0=f0,
        is_valid=is_valid,
        ratio=reduced_fraction,
        a=reduced_a,
        b=reduced_b,
        gcd_value=g,
        error=relative_error,
        max_denominator=max_denominator,
        in_grid=in_grid,
    )


def verify_grid_integrity(
    channels: List[Dict[str, Any]],
    f0: float,
    tolerance: float = 1e-4,
    max_denominator: int = 16,
) -> Dict[str, Any]:
    """Verify the integrity of a set of channels against the HPG grid.

    Checks that all channel frequencies correspond to valid rational
    harmonics in H_N.

    Args:
        channels: List of channel dictionaries with "frequency_hz" key.
        f0: Fundamental frequency (Hz).
        tolerance: Maximum relative error for verification.
        max_denominator: Maximum denominator N for H_N.

    Returns:
        Dictionary with overall integrity status and per-channel results.
    """
    results = []
    all_valid = True
    invalid_count = 0

    for ch in channels:
        freq = ch.get("frequency_hz", 0.0)
        if freq <= 0:
            results.append({
                "channel": ch.get("id", "unknown"),
                "valid": False,
                "reason": "Non-positive frequency",
            })
            all_valid = False
            invalid_count += 1
            continue

        vr = verify_rational_ratio(freq, f0, tolerance, max_denominator)
        if not vr.is_valid:
            all_valid = False
            invalid_count += 1
            results.append({
                "channel": ch.get("id", "unknown"),
                "frequency": freq,
                "valid": False,
                "reason": f"Ratio {vr.ratio} not in H_{max_denominator} "
                          f"(error={vr.error:.6f})",
            })
        else:
            results.append({
                "channel": ch.get("id", "unknown"),
                "frequency": freq,
                "valid": True,
                "ratio": str(vr.ratio),
                "error": vr.error,
            })

    return {
        "f0_hz": f0,
        "max_denominator": max_denominator,
        "total_channels": len(channels),
        "valid_channels": len(channels) - invalid_count,
        "invalid_channels": invalid_count,
        "all_valid": all_valid,
        "details": results,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Spectral Verification - Example Usage")
    print("=" * 60)

    f0 = 16384.0

    print(f"\nf0 = {f0} Hz")
    print("\nVerifying valid harmonic frequencies:")

    test_freqs = [
        (f0 * 1, "1/1 fundamental"),
        (f0 * 1 / 2, "1/2 half"),
        (f0 * 2 / 3, "2/3 two-thirds"),
        (f0 * 3 / 5, "3/5 three-fifths"),
        (f0 * 5 / 6, "5/6 five-sixths"),
        (f0 * 1.4142, "sqrt(2) - IRRATIONAL"),
        (f0 * 0.3, "0.3 - not harmonic"),
        (12345.67, "arbitrary frequency"),
    ]

    for freq, label in test_freqs:
        result = verify_rational_ratio(freq, f0, tolerance=1e-3)
        status = "VALID" if result.is_valid else "INVALID"
        ratio_str = str(result.ratio) if result.ratio else "N/A"
        print(
            f"  [{status:7s}] {freq:12.2f} Hz ({label:25s}) "
            f"-> {ratio_str:>5s}  err={result.error:.6f}  "
            f"in_grid={result.in_grid}"
        )

    print("\n" + "-" * 60)
    print("Grid integrity check for HPM 1.0 channels:")

    hpm_channels = [
        {"id": 0, "frequency_hz": f0 * 1.0},
        {"id": 1, "frequency_hz": f0 * 1 / 2},
        {"id": 2, "frequency_hz": f0 * 1 / 3},
        {"id": 3, "frequency_hz": f0 * 2 / 3},
        {"id": 4, "frequency_hz": f0 * 1 / 4},
        {"id": 5, "frequency_hz": f0 * 3 / 4},
        {"id": 6, "frequency_hz": f0 * 1 / 5},
        {"id": 7, "frequency_hz": f0 * 2 / 5},
        {"id": 8, "frequency_hz": f0 * 3 / 5},
        {"id": 9, "frequency_hz": f0 * 4 / 5},
        {"id": 10, "frequency_hz": f0 * 1 / 6},
        {"id": 11, "frequency_hz": f0 * 5 / 6},
    ]

    integrity = verify_grid_integrity(hpm_channels, f0)
    print(f"  All valid: {integrity['all_valid']}")
    print(f"  Valid: {integrity['valid_channels']}/{integrity['total_channels']}")
    for detail in integrity["details"]:
        status = "OK" if detail["valid"] else "FAIL"
        print(f"    CH{detail['channel']:2d}: [{status:4s}] {detail.get('ratio', detail.get('reason', ''))}")