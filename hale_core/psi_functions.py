"""PSI Addressing Functions.

THEORETICAL REFERENCE (CC BY-NC-ND 4.0 - NO CODE DERIVATIVES):
    DOI: 10.5281/zenodo.18901934 - HALE Working Paper v3.0
    The concept of 4 psi functions (psi1-psi4) is referenced
    as theoretical motivation only.

IMPLEMENTATION BASED ON (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid
    All implementations use HPG 1.0 definitions independently.

This module provides four selectable addressing (psi) functions
for the HALE pipeline:
    psi1: Direct index mapping from harmonic ratio to grid index.
    psi2: Binary activation pattern based on denominator parity.
    psi3: Prime factorization addressing using denominator decomposition.
    psi4: Learned/weighted addressing (heuristic scoring).
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from hale_core.hale_equation import ChannelAddress


def _prime_factors(n: int) -> List[int]:
    """Return the sorted list of prime factors of n (with repetitions).

    Examples:
        >>> _prime_factors(12)
        [2, 2, 3]
        >>> _prime_factors(7)
        [7]
        >>> _prime_factors(1)
        []
    """
    factors: List[int] = []
    if n < 2:
        return factors
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def psi1_direct(addr: ChannelAddress) -> ChannelAddress:
    """Psi 1: Direct Index Mapping.

    Maps the harmonic ratio a/b directly to its linear grid index.
    This is the identity addressing function: it returns the input
    address unchanged, using the pre-computed grid index.

    The index is derived from the enumeration order of H_N x {-1, +1},
    where elements are ordered by (b, a, polarity).

    Args:
        addr: Input ChannelAddress from the grid.

    Returns:
        The same ChannelAddress (identity mapping).
    """
    return ChannelAddress(
        index=addr.index,
        a=addr.a,
        b=addr.b,
        polarity=addr.polarity,
    )


def psi2_binary(addr: ChannelAddress) -> ChannelAddress:
    """Psi 2: Binary Activation Pattern.

    Produces a binary activation pattern based on the denominator
    of the harmonic ratio. The polarity is determined by:
        - If b is even: polarity = +1 (activated)
        - If b is odd:  polarity = -1 (deactivated)

    This creates a natural alternating pattern in the Omnigrid
    based on denominator parity, useful for even-odd channel grouping.

    The index is remapped as: index = a * b + (0 if b is even else 1)

    Args:
        addr: Input ChannelAddress from the grid.

    Returns:
        Transformed ChannelAddress with parity-based polarity and index.
    """
    new_polarity = 1 if addr.b % 2 == 0 else -1
    new_index = addr.a * addr.b + (0 if addr.b % 2 == 0 else 1)
    return ChannelAddress(
        index=new_index,
        a=addr.a,
        b=addr.b,
        polarity=new_polarity,
    )


def psi3_prime(addr: ChannelAddress) -> ChannelAddress:
    """Psi 3: Prime Factorization Addressing.

    Uses the prime factorization of the denominator b to compute
    an addressing key. The index is derived from the sum of distinct
    prime factors of b, scaled by the numerator a.

    For denominator b with distinct prime factors {p1, p2, ..., pk}:
        key = a * (p1 + p2 + ... + pk)

    The polarity is set to +1 if the number of distinct prime
    factors is even, and -1 if odd.

    This function leverages the multiplicative structure of the
    harmonic ratios for structured addressing.

    Args:
        addr: Input ChannelAddress from the grid.

    Returns:
        Transformed ChannelAddress with prime-factor-based addressing.
    """
    distinct_primes = set(_prime_factors(addr.b))
    prime_sum = sum(distinct_primes)
    new_index = addr.a * prime_sum if prime_sum > 0 else addr.index
    new_polarity = 1 if len(distinct_primes) % 2 == 0 else -1
    return ChannelAddress(
        index=new_index,
        a=addr.a,
        b=addr.b,
        polarity=new_polarity,
    )


def psi4_learned(addr: ChannelAddress) -> ChannelAddress:
    """Psi 4: Learned / Weighted Addressing.

    A heuristic addressing function that computes a weighted score
    for each channel based on:
        - Channel priority: P(a/b) = 1/(a+b)
        - Denominator magnitude: larger b values get lower weight
        - Numerator-denominator balance: |a - b| affects the score

    The weighted score determines the remapped index:
        score = P(a/b) * (1 + 1/b) * (1 / (1 + |a - b|))
        index = round(score * 1000)

    Polarity is +1 when a > b (superharmonic) and -1 when a < b
    (subharmonic).

    This function can be replaced with a trained model in production.

    Args:
        addr: Input ChannelAddress from the grid.

    Returns:
        Transformed ChannelAddress with weighted addressing.
    """
    priority = addr.priority
    balance_factor = 1.0 / (1 + abs(addr.a - addr.b))
    denom_weight = 1.0 + 1.0 / addr.b
    score = priority * denom_weight * balance_factor
    new_index = round(score * 10000)

    if addr.a > addr.b:
        new_polarity = 1
    elif addr.a < addr.b:
        new_polarity = -1
    else:
        new_polarity = addr.polarity

    return ChannelAddress(
        index=new_index,
        a=addr.a,
        b=addr.b,
        polarity=new_polarity,
    )


PSI_FUNCTIONS: Dict[str, type] = {
    "psi1": psi1_direct,
    "psi2": psi2_binary,
    "psi3": psi3_prime,
    "psi4": psi4_learned,
}


def get_psi_function(name: str):
    """Retrieve a psi function by name.

    Args:
        name: One of "psi1", "psi2", "psi3", "psi4".

    Returns:
        The corresponding psi function.

    Raises:
        ValueError: If name is not a valid psi function name.
    """
    if name not in PSI_FUNCTIONS:
        valid = ", ".join(PSI_FUNCTIONS.keys())
        raise ValueError(f"Unknown psi function: {name}. Valid: {valid}")
    return PSI_FUNCTIONS[name]


if __name__ == "__main__":
    from hale_core.hale_equation import ChannelAddress

    print("=" * 60)
    print("PSI Addressing Functions - Example Usage")
    print("=" * 60)

    test_addresses = [
        ChannelAddress(index=0, a=1, b=1, polarity=1),
        ChannelAddress(index=2, a=1, b=3, polarity=1),
        ChannelAddress(index=4, a=2, b=3, polarity=1),
        ChannelAddress(index=6, a=1, b=4, polarity=1),
        ChannelAddress(index=10, a=3, b=4, polarity=1),
        ChannelAddress(index=14, a=2, b=5, polarity=1),
    ]

    print(f"\nInput addresses:")
    for addr in test_addresses:
        print(f"  {addr}")

    for name in ["psi1", "psi2", "psi3", "psi4"]:
        func = get_psi_function(name)
        desc = {
            "psi1": "Direct Index",
            "psi2": "Binary Activation",
            "psi3": "Prime Factorization",
            "psi4": "Learned / Weighted",
        }
        print(f"\n{name}: {desc[name]}")
        print("-" * 50)
        for addr in test_addresses:
            result = func(addr)
            print(
                f"  {addr.a}/{addr.b} -> "
                f"idx={result.index:4d}, pol={result.polarity:+d}, "
                f"P={result.priority:.4f}"
            )

    print("\n" + "=" * 60)
    print("Prime factorization examples:")
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16]:
        pf = _prime_factors(n)
        dpf = set(pf)
        print(f"  b={n:2d}: factors={pf}, distinct={sorted(dpf)}")