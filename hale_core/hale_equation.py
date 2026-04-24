"""HALE Equation Pipeline.

THEORETICAL REFERENCE (CC BY-NC-ND 4.0 - NO CODE DERIVATIVES):
    DOI: 10.5281/zenodo.18901934 - HALE Working Paper v3.0
    Core HALE equation: g = M[psi(h)] = M[psi(f0/d1, f0/d2, ..., f0/dn)]
    Pipeline: f0 -> H (quantization) -> h vector -> psi (addressing)
              -> c vector -> M (lookup) -> g

    The HALE equation is referenced SOLELY as theoretical motivation.
    No code in this module is derived from Paper 1.

IMPLEMENTATION BASED ON (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid
    Rational Harmonic Subdivision Set: H_N = {a/b in Q+ : gcd(a,b)=1, b<=N, a<=N}
    Omnigrid: O_N = H_N x {-1, +1}
    Channel Priority: P(a/b) = 1/(a+b)

This module implements an independent harmonic addressing pipeline
using the HPG 1.0 definitions for rational harmonic subdivision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from fractions import Fraction


@dataclass
class HarmonicVector:
    """Represents a harmonic vector h = [f0/d1, f0/d2, ..., f0/dn].

    Attributes:
        f0: Fundamental frequency in Hz.
        divisors: List of positive integer divisors d1, d2, ..., dn.
        ratios: Computed rational ratios [1/d1, 1/d2, ..., 1/dn].
    """

    f0: float
    divisors: List[int]
    ratios: List[Fraction] = field(init=False)

    def __post_init__(self) -> None:
        for d in self.divisors:
            if d <= 0:
                raise ValueError(f"Divisor must be positive, got {d}")
        self.ratios = [Fraction(1, d) for d in self.divisors]

    def get_frequencies(self) -> List[float]:
        """Return the actual frequencies [f0/d1, f0/d2, ..., f0/dn]."""
        return [self.f0 * float(r) for r in self.ratios]

    def __repr__(self) -> str:
        ratios_str = ", ".join(str(r) for r in self.ratios)
        return f"HarmonicVector(f0={self.f0}, ratios=[{ratios_str}])"


@dataclass
class ChannelAddress:
    """Represents a channel address in the 2D harmonic Omnigrid.

    Attributes:
        index: Linear index in the grid.
        a: Numerator of the rational harmonic ratio.
        b: Denominator of the rational harmonic ratio.
        polarity: Sign dimension in the Omnigrid (-1 or +1).
        ratio: Computed rational ratio a/b.
        priority: Channel priority P(a/b) = 1/(a+b).
    """

    index: int
    a: int
    b: int
    polarity: int
    ratio: Fraction = field(init=False)
    priority: float = field(init=False)

    def __post_init__(self) -> None:
        if self.polarity not in (-1, 1):
            raise ValueError(f"Polarity must be -1 or +1, got {self.polarity}")
        self.ratio = Fraction(self.a, self.b)
        self.priority = 1.0 / (self.a + self.b)

    def frequency(self, f0: float) -> float:
        """Compute the actual frequency for a given f0."""
        return f0 * float(self.ratio)

    def __repr__(self) -> str:
        return (
            f"ChannelAddress(idx={self.index}, {self.a}/{self.b}, "
            f"pol={self.polarity:+d}, P={self.priority:.4f})"
        )


class HALEPipeline:
    """Harmonic Addressing Pipeline based on HPG 1.0 definitions.

    The HALE equation g = M[psi(h)] is referenced from Paper 1
    (DOI: 10.5281/zenodo.18901934, CC BY-NC-ND 4.0) as theoretical
    motivation only. This implementation is independently based on
    the HPG 1.0 definitions from Paper 4
    (DOI: 10.5281/zenodo.19056387, CC BY 4.0).

    Pipeline stages:
        1. f0 (fundamental frequency)
        2. H (quantization): Divide f0 by divisors to produce harmonic vector h
        3. h (harmonic vector): List of rational ratios 1/d_i
        4. psi (addressing): Map harmonic ratios to grid channel addresses
        5. c (channel vector): List of ChannelAddress objects
        6. M (lookup): Retrieve channel configurations from the grid
        7. g (output): Final grid mapping with frequencies and priorities

    Args:
        f0: Fundamental frequency in Hz.
        max_denominator: Maximum denominator N for H_N construction.
        psi_func: Optional custom addressing function psi(ChannelAddress) -> ChannelAddress.
    """

    def __init__(
        self,
        f0: float,
        max_denominator: int = 16,
        psi_func: Optional[Callable[[ChannelAddress], ChannelAddress]] = None,
    ) -> None:
        if f0 <= 0:
            raise ValueError(f"f0 must be positive, got {f0}")
        if max_denominator < 1:
            raise ValueError(f"max_denominator must be >= 1, got {max_denominator}")
        self.f0 = f0
        self.max_denominator = max_denominator
        self.psi_func = psi_func
        self._grid: Dict[Tuple[int, int, int], ChannelAddress] = self._build_grid()

    def _build_grid(self) -> Dict[Tuple[int, int, int], ChannelAddress]:
        """Build the 2D Omnigrid O_N = H_N x {-1, +1}.

        Returns:
            Dictionary mapping (a, b, polarity) to ChannelAddress.
        """
        grid: Dict[Tuple[int, int, int], ChannelAddress] = {}
        idx = 0
        for b in range(1, self.max_denominator + 1):
            for a in range(1, self.max_denominator + 1):
                if math.gcd(a, b) == 1:
                    for polarity in (-1, +1):
                        grid[(a, b, polarity)] = ChannelAddress(
                            index=idx, a=a, b=b, polarity=polarity
                        )
                        idx += 1
        return grid

    @property
    def grid_size(self) -> int:
        """Total number of addresses in the Omnigrid O_N."""
        return len(self._grid)

    @property
    def channel_count(self) -> int:
        """Number of unique rational harmonics |H_N|."""
        return self.grid_size // 2

    def quantize(self, divisors: List[int]) -> HarmonicVector:
        """Step H: Quantize f0 by divisors to produce harmonic vector h.

        Given f0 and a list of divisors [d1, d2, ..., dn], computes
        the harmonic vector h = [f0/d1, f0/d2, ..., f0/dn].

        Args:
            divisors: List of positive integers to divide f0.

        Returns:
            HarmonicVector containing the ratios and frequencies.
        """
        return HarmonicVector(f0=self.f0, divisors=divisors)

    def address(self, h: HarmonicVector) -> List[ChannelAddress]:
        """Step psi: Apply addressing function to map h to channel indices.

        For each ratio 1/d in the harmonic vector, finds the corresponding
        channel in the Omnigrid. If a custom psi function is provided,
        it is applied to transform the address.

        Args:
            h: Harmonic vector from the quantization step.

        Returns:
            List of ChannelAddress objects in the grid.
        """
        addresses: List[ChannelAddress] = []
        for ratio in h.ratios:
            a, b = ratio.numerator, ratio.denominator
            key = (a, b, 1)
            if key not in self._grid:
                continue
            addr = self._grid[key]
            if self.psi_func is not None:
                addr = self.psi_func(addr)
            addresses.append(addr)
        return addresses

    def lookup(self, addresses: List[ChannelAddress]) -> Dict[str, Any]:
        """Step M: Look up channel configurations from the grid.

        For each channel address, retrieves the frequency, ratio,
        priority, and other metadata.

        Args:
            addresses: List of ChannelAddress objects.

        Returns:
            Dictionary with grid metadata and channel configurations.
        """
        channels: List[Dict[str, Any]] = []
        for addr in addresses:
            freq = addr.frequency(self.f0)
            channels.append({
                "index": addr.index,
                "a": addr.a,
                "b": addr.b,
                "ratio": f"{addr.a}/{addr.b}",
                "frequency": freq,
                "priority": addr.priority,
                "polarity": addr.polarity,
            })
        channels.sort(key=lambda c: c["frequency"])
        return {
            "f0": self.f0,
            "max_denominator": self.max_denominator,
            "grid_size": self.grid_size,
            "channel_count": self.channel_count,
            "active_channels": len(channels),
            "channels": channels,
        }

    def execute(self, divisors: List[int]) -> Dict[str, Any]:
        """Execute the full HALE pipeline.

        Computes: g = M[psi(H(f0, divisors))]

        This is the complete pipeline:
            f0 -> quantize -> h -> address -> c -> lookup -> g

        Args:
            divisors: List of positive integer divisors.

        Returns:
            Final grid mapping with all channel metadata.
        """
        h = self.quantize(divisors)
        c = self.address(h)
        g = self.lookup(c)
        g["h_vector"] = [str(r) for r in h.ratios]
        g["pipeline"] = "HALE: f0 -> H -> h -> psi -> c -> M -> g"
        return g


if __name__ == "__main__":
    print("=" * 60)
    print("HALE Equation Pipeline - Example Usage")
    print("=" * 60)

    # Example 1: Basic pipeline with f0 = 16.384 kHz (HPM 1.0)
    pipeline = HALEPipeline(f0=16384.0, max_denominator=16)
    print(f"\nf0 = {pipeline.f0} Hz")
    print(f"Grid size O_16 = {pipeline.grid_size} addresses")
    print(f"Channel count H_16 = {pipeline.channel_count} channels")

    result = pipeline.execute(divisors=[1, 2, 3, 4, 5, 6])
    print(f"\nActive channels: {result['active_channels']}")
    print(f"Pipeline: {result['pipeline']}")
    print(f"h_vector: {result['h_vector']}")
    print("\nChannel mapping:")
    for ch in result["channels"]:
        print(
            f"  [{ch['index']:3d}] {ch['ratio']:>4s} -> "
            f"{ch['frequency']:10.2f} Hz  (P={ch['priority']:.4f})"
        )

    # Example 2: IoT at f0 = 868 MHz (16 channels)
    print("\n" + "-" * 60)
    iot_pipeline = HALEPipeline(f0=868e6, max_denominator=16)
    divisors_iot = list(range(1, 17))
    iot_result = iot_pipeline.execute(divisors=divisors_iot)
    print(f"\nIoT f0 = 868 MHz, {iot_result['active_channels']} channels")
    print("First 5 channels:")
    for ch in iot_result["channels"][:5]:
        freq_mhz = ch["frequency"] / 1e6
        print(
            f"  {ch['ratio']:>4s} -> {freq_mhz:12.4f} MHz  "
            f"(P={ch['priority']:.4f})"
        )

    # Example 3: Resynchronization period
    print("\n" + "-" * 60)
    print("Resynchronization periods (T_sync = lcm(b1,b2) / f0):")
    from math import lcm as math_lcm
    b_values = [ch["b"] for ch in result["channels"][:4]]
    if len(b_values) >= 2:
        l = math_lcm(b_values[0], b_values[1])
        t_sync = l / pipeline.f0
        print(f"  lcm({b_values[0]}, {b_values[1]}) = {l}")
        print(f"  T_sync = {l} / {pipeline.f0} = {t_sync:.6f} s")