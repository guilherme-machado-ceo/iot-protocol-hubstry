"""Psi addressing functions (ψ1-ψ4).

Selectable functions for device addressing within the HALE pipeline.
Each function maps a harmonic ratio a/b to a scalar address in [0, 1).
"""

from math import gcd, log, pi, sin, cos, sqrt
from fractions import Fraction


def psi1(a: int, b: int, f0: float) -> float:
    """Direct ratio mapping.

    Maps a/b to a normalized value in [0, 1) scaled by f0.

    ψ₁(a/b) = (a/b) / N  where N is the max denominator.
    Simplified: a / b.
    """
    return Fraction(a, b) / f0


def psi2(a: int, b: int, f0: float) -> float:
    """Euler totient-based mapping.

    Uses the totient of the denominator to weight the address.
    ψ₂(a/b) = φ(b) / (b · f0)
    """
    phi_b = euler_totient(b)
    return Fraction(a * phi_b, b) / f0


def psi3(a: int, b: int, f0: float) -> float:
    """Trigonometric projection.

    Projects the harmonic ratio onto a circular phase space.
    ψ₃(a/b) = sin(2π · a/b) · cos(2π · b/f0)
    """
    ratio = a / b
    return (sin(2 * pi * ratio) * cos(2 * pi * b / f0)) % 1.0


def psi4(a: int, b: int, f0: float) -> float:
    """Composite spectral address.

    Combines ratio, totient weight, and phase into a single scalar.
    ψ₄(a/b) = (a/b + φ(b)/b + sin(2π·a/b)) / 3  mod 1
    """
    ratio = a / b
    phi_b = euler_totient(b)
    return ((ratio + phi_b / b + sin(2 * pi * ratio)) / 3.0) % 1.0


def euler_totient(n: int) -> int:
    """Compute Euler's totient function φ(n).

    φ(n) counts the positive integers up to n that are coprime with n.
    """
    if n <= 0:
        return 0
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


__all__ = ["psi1", "psi2", "psi3", "psi4", "euler_totient"]
