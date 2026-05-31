"""HALE Pipeline: f0 → H → h → ψ → c → M → g.

The core addressing pipeline for the Nautam IoT protocol.
Takes a fundamental frequency f0 and produces a grid of
addressable harmonic channels with metadata.

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd, lcm
from typing import Callable, Dict, List, Optional, Tuple

from .psi_functions import euler_totient, psi1, psi2, psi3, psi4


@dataclass
class HarmonicChannel:
    """A single harmonic channel in the HALE grid.

    Attributes:
        a: Numerator of the harmonic ratio.
        b: Denominator of the harmonic ratio.
        ratio: Fraction a/b.
        frequency_hz: Absolute frequency = (a/b) * f0.
        priority: Channel priority P(a/b) = 1/(a+b).
        psi_value: Addressing function output.
        address_code: Final address label.
        polarity: Sign in the Omnigrid (+1 or -1).
    """

    a: int
    b: int
    ratio: Fraction
    frequency_hz: float
    priority: float
    psi_value: float
    address_code: str
    polarity: int = 1

    @property
    def label(self) -> str:
        return f"H{self.a}/{self.b}"


@dataclass
class HALEPipelineResult:
    """Result of executing the HALE pipeline.

    Attributes:
        f0: Fundamental frequency used.
        max_denominator: N parameter for H_N.
        grid: List of HarmonicChannel objects.
        grid_size: Number of channels in H_N.
        omnigrid_size: Number of addresses in O_N (2 × grid_size).
        resync_period: T_sync = lcm(b1, b2, ...) / f0.
        cardinality: |H_N| = Σ φ(b).
    """

    f0: float
    max_denominator: int
    grid: List[HarmonicChannel] = field(default_factory=list)
    grid_size: int = 0
    omnigrid_size: int = 0
    resync_period: float = 0.0
    cardinality: int = 0


class HALEPipeline:
    """HALE Pipeline: f0 → H → h → ψ → c → M → g.

    Steps:
        1. f0: Fundamental frequency (master frequency).
        2. H: Compute H_N = {a/b : gcd(a,b)=1, b<=N, a<=N}.
        3. h: Compute cardinality |H_N| = Σ φ(b).
        4. ψ: Apply addressing function to each ratio.
        5. c: Compute absolute frequencies and priorities.
        6. M: Generate address codes.
        7. g: Build the final grid with metadata.

    Args:
        f0: Fundamental frequency in Hz (default: 16384.0).
        max_denominator: N parameter for H_N (default: 16).
        psi_function: Addressing function (default: psi1).
    """

    PSI_FUNCTIONS = {
        "psi1": psi1,
        "psi2": psi2,
        "psi3": psi3,
        "psi4": psi4,
    }

    def __init__(
        self,
        f0: float = 16384.0,
        max_denominator: int = 16,
        psi_function: Optional[Callable] = None,
    ):
        self.f0 = f0
        self.max_denominator = max_denominator
        self.psi_function = psi_function or psi1

    def compute_hn(self) -> List[Tuple[int, int]]:
        """Step 1-2: Compute the rational harmonic set H_N.

        H_N = {a/b ∈ Q⁺ : gcd(a, b) = 1, b ≤ N, a ≤ N}

        Returns:
            List of (a, b) tuples sorted by ratio value.
        """
        ratios = set()
        N = self.max_denominator
        for b in range(1, N + 1):
            for a in range(1, N + 1):
                if gcd(a, b) == 1:
                    ratios.add((a, b))
        return sorted(ratios, key=lambda x: Fraction(x[0], x[1]))

    def compute_cardinality(self) -> int:
        """Step 3: Compute |H_N| = Σ φ(b) for b=1..N."""
        return sum(euler_totient(b) for b in range(1, self.max_denominator + 1))

    def execute(
        self,
        divisors: Optional[List[int]] = None,
        polarity: int = 1,
    ) -> HALEPipelineResult:
        """Execute the full HALE pipeline.

        Args:
            divisors: Optional list of divisors to filter. If None, use all from H_N.
            polarity: Omnigrid polarity (+1 or -1).

        Returns:
            HALEPipelineResult with all channel data.
        """
        # Step 1-2: Compute H_N
        hn = self.compute_hn()

        # Filter by divisors if provided
        if divisors:
            hn = [(a, b) for a, b in hn if b in divisors]

        # Step 3: Cardinality
        cardinality = self.compute_cardinality()

        # Steps 4-7: Build grid
        grid = []
        for a, b in hn:
            ratio = Fraction(a, b)
            frequency = (a / b) * self.f0
            priority = 1.0 / (a + b)
            psi_val = self.psi_function(a, b, self.f0)

            # Generate address code (hash-based for uniqueness)
            raw = f"{a}/{b}:{self.f0}:{psi_val:.8f}"
            addr_hash = hashlib.sha256(raw.encode()).hexdigest()[:12]

            channel = HarmonicChannel(
                a=a,
                b=b,
                ratio=ratio,
                frequency_hz=frequency,
                priority=priority,
                psi_value=psi_val,
                address_code=addr_hash,
                polarity=polarity,
            )
            grid.append(channel)

        # Compute resync period
        denominators = [b for _, b in hn]
        if denominators:
            t_sync = lcm(*denominators) / self.f0
        else:
            t_sync = 0.0

        return HALEPipelineResult(
            f0=self.f0,
            max_denominator=self.max_denominator,
            grid=grid,
            grid_size=len(grid),
            omnigrid_size=len(grid) * 2,
            resync_period=t_sync,
            cardinality=cardinality,
        )


__all__ = ["HALEPipeline", "HALEPipelineResult", "HarmonicChannel"]
