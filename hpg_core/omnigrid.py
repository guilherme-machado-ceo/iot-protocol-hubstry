"""Omnigrid 2D: H_N × {-1, +1}.

The Omnigrid extends the harmonic set H_N into a 2D address space
by adding a polarity dimension. This doubles the addressable space.

O_N = H_N × {-1, +1}
|O_N| = 2 × |H_N|

Reference: DOI 10.5281/zenodo.19056387 (CC BY 4.0)
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from typing import Dict, List, Set, Tuple

from hale_core.psi_functions import euler_totient


def compute_hn(N: int = 16) -> Set[Fraction]:
    """Compute the rational harmonic subdivision set H_N.

    H_N = {a/b ∈ Q⁺ : gcd(a, b) = 1, b ≤ N, a ≤ N}

    Args:
        N: Maximum denominator (default: 16).

    Returns:
        Set of unique Fraction objects representing H_N.
    """
    hn = set()
    for b in range(1, N + 1):
        for a in range(1, N + 1):
            if gcd(a, b) == 1:
                hn.add(Fraction(a, b))
    return hn


def cardinality_hn(N: int = 16) -> int:
    """Compute |H_N| = Σ φ(b) for b = 1..N.

    Uses Euler's totient function.

    Args:
        N: Maximum denominator (default: 16).

    Returns:
        Cardinality of H_N. For N=16, returns 80.
    """
    return sum(euler_totient(b) for b in range(1, N + 1))


def omnigrid_2d(N: int = 16) -> List[Dict]:
    """Build the 2D Omnigrid O_N = H_N × {-1, +1}.

    Each harmonic ratio gets two addresses: one positive, one negative.
    This creates a bidimensional address space suitable for
    dual-polarity signaling (e.g., amplitude modulation).

    Args:
        N: Maximum denominator (default: 16).

    Returns:
        List of dicts with keys: ratio, a, b, polarity, address_id.
        Sorted by ratio value then polarity.
    """
    hn = sorted(compute_hn(N), key=lambda f: float(f))
    grid = []
    for idx, ratio in enumerate(hn):
        a, b = ratio.numerator, ratio.denominator
        for polarity in (1, -1):
            grid.append({
                "id": idx * 2 + (0 if polarity == 1 else 1),
                "ratio": ratio,
                "a": a,
                "b": b,
                "polarity": polarity,
                "address_id": f"O({a}/{b}, {'+' if polarity == 1 else '-'})",
            })
    return grid


__all__ = ["compute_hn", "cardinality_hn", "omnigrid_2d"]
