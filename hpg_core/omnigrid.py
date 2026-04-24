"""2D Harmonic Omnigrid with Euler Totient Computation.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

Mathematical definitions:
    Rational Harmonic Subdivision Set:
        H_N = {a/b in Q+ : gcd(a,b)=1, b<=N, a<=N}

    Cardinality:
        |H_N| = sum(phi(b)) for b=1 to N
        where phi is Euler totient function

    Omnigrid (2D address space):
        O_N = H_N x {-1, +1}
        |O_N| = 2 * |H_N|

    Channel Priority:
        P(a/b) = 1 / (a + b)

Example: |H_16| = 80 channels, |O_16| = 160 addresses.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Set, Tuple


def euler_totient(n: int) -> int:
    """Compute Euler totient function phi(n).

    Euler totient phi(n) counts the positive integers up to n
    that are coprime with n.

    Algorithm:
        phi(n) = n * product(1 - 1/p for each distinct prime p dividing n)

    Args:
        n: Positive integer.

    Returns:
        Euler totient of n.

    Examples:
        >>> euler_totient(1)
        1
        >>> euler_totient(12)
        4
        >>> euler_totient(16)
        8
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    result = n
    temp = n
    p = 2
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


def cardinality_hn(n: int) -> int:
    """Compute the cardinality |H_N|.

    |H_N| = sum(phi(b)) for b = 1 to N

    This counts the number of reduced fractions a/b with
    gcd(a,b)=1, 1 <= b <= N, 1 <= a <= N.

    Args:
        n: Maximum denominator N.

    Returns:
        Total number of elements in H_N.

    Examples:
        >>> cardinality_hn(1)
        1
        >>> cardinality_hn(6)
        15
        >>> cardinality_hn(16)
        80
    """
    return sum(euler_totient(b) for b in range(1, n + 1))


def compute_hn(n: int) -> List[Tuple[int, int, Fraction]]:
    """Compute the Rational Harmonic Subdivision Set H_N.

    H_N = {a/b in Q+ : gcd(a,b)=1, b<=N, a<=N}

    Elements are returned sorted by (denominator, numerator)
    for deterministic ordering.

    Args:
        n: Maximum denominator N.

    Returns:
        List of (a, b, Fraction) tuples in sorted order.

    Examples:
        >>> hn = compute_hn(4)
        >>> len(hn)
        8
        >>> hn[0]
        (1, 1, Fraction(1, 1))
    """
    elements: List[Tuple[int, int, Fraction]] = []
    for b in range(1, n + 1):
        for a in range(1, n + 1):
            if math.gcd(a, b) == 1:
                elements.append((a, b, Fraction(a, b)))
    elements.sort(key=lambda x: (x[1], x[0]))
    return elements


@dataclass
class OmnigridAddress:
    """A 2D address in the Omnigrid O_N = H_N x {-1, +1}.

    Attributes:
        a: Numerator of the harmonic ratio.
        b: Denominator of the harmonic ratio.
        polarity: Sign dimension (-1 or +1).
        ratio: Computed rational ratio a/b.
        linear_index: Pre-computed linear index for array access.
        priority: Channel priority P(a/b) = 1/(a+b).
    """

    a: int
    b: int
    polarity: int
    linear_index: int = 0
    ratio: Fraction = Fraction(0, 1)
    priority: float = 0.0

    def __post_init__(self) -> None:
        if self.polarity not in (-1, 1):
            raise ValueError(f"Polarity must be -1 or +1, got {self.polarity}")
        self.ratio = Fraction(self.a, self.b)
        self.priority = 1.0 / (self.a + self.b)

    def frequency(self, f0: float) -> float:
        """Compute the actual frequency: f = (a/b) * f0."""
        return float(self.ratio) * f0

    def __repr__(self) -> str:
        return (
            f"Omnigrid({self.a}/{self.b}, pol={self.polarity:+d}, "
            f"idx={self.linear_index}, P={self.priority:.4f})"
        )


def omnigrid_2d(n: int) -> List[OmnigridAddress]:
    """Build the 2D Harmonic Omnigrid O_N = H_N x {-1, +1}.

    The Omnigrid expands the harmonic set H_N into a 2D address
    space by combining each rational harmonic with a polarity
    dimension. This doubles the address space:
        |O_N| = 2 * |H_N|

    For N=16: |O_16| = 2 * 80 = 160 addresses.

    Args:
        n: Maximum denominator N.

    Returns:
        List of OmnigridAddress objects sorted by (b, a, polarity).
    """
    hn = compute_hn(n)
    addresses: List[OmnigridAddress] = []
    linear_idx = 0
    for a, b, _ in hn:
        for pol in (-1, +1):
            addr = OmnigridAddress(
                a=a, b=b, polarity=pol, linear_index=linear_idx
            )
            addresses.append(addr)
            linear_idx += 1
    return addresses


def compute_resync_period(denominators: List[int], f0: float) -> float:
    """Compute the natural re-synchronization period.

    T_sync = lcm(b1, b2, ..., bn) / f0

    This is the period after which all harmonic channels
    simultaneously return to their initial phase alignment.

    Args:
        denominators: List of denominators b1, b2, ..., bn.
        f0: Fundamental frequency in Hz.

    Returns:
        Re-synchronization period in seconds.
    """
    if not denominators:
        return 0.0
    l = denominators[0]
    for b in denominators[1:]:
        l = (l * b) // math.gcd(l, b)
    return l / f0


if __name__ == "__main__":
    print("=" * 60)
    print("Harmonic Omnigrid - Example Usage")
    print("=" * 60)

    # Euler totient values for b = 1 to 16
    print("\nEuler totient phi(b) for b = 1..16:")
    phi_values = [euler_totient(b) for b in range(1, 17)]
    for b, phi in enumerate(phi_values, start=1):
        print(f"  phi({b:2d}) = {phi:2d}")
    print(f"  Sum    = {sum(phi_values)}")

    # Cardinality
    for n in [4, 8, 12, 16]:
        c = cardinality_hn(n)
        print(f"\n|H_{n}| = {c}, |O_{n}| = {2 * c}")

    # Compute H_16
    print("\n" + "-" * 60)
    h16 = compute_hn(16)
    print(f"H_16 has {len(h16)} elements")
    print("First 10 elements:")
    for a, b, frac in h16[:10]:
        print(f"  {a}/{b} = {float(frac):.6f}")
    print("Last 5 elements:")
    for a, b, frac in h16[-5:]:
        print(f"  {a}/{b} = {float(frac):.6f}")

    # Omnigrid
    print("\n" + "-" * 60)
    o16 = omnigrid_2d(16)
    print(f"O_16 has {len(o16)} addresses")
    print("First 5 addresses:")
    for addr in o16[:5]:
        freq = addr.frequency(16384.0)
        print(f"  {addr}  freq={freq:.2f} Hz")

    # Resynchronization period
    print("\n" + "-" * 60)
    f0 = 16384.0
    dens = [2, 3, 4, 5]
    t_sync = compute_resync_period(dens, f0)
    l_val = 60
    for b in dens[1:]:
        l_val = (l_val * b) // math.gcd(l_val, b)
    print(f"Denominators: {dens}")
    print(f"lcm = {l_val}")
    print(f"T_sync = {l_val} / {f0} = {t_sync:.6f} s")