"""HPM 1.0 — Harmonic Protocol Multiplexer channel configuration.

Defines 12 harmonic channels derived from a fundamental frequency
of f0 = 16.384 kHz. Each channel uses a rational harmonic ratio
from the H_N set.

Reference: DOI 10.5281/zenodo.19056387 (CC BY 4.0)
"""

from __future__ import annotations

from typing import Dict, List


class HPM10Config:
    """HPM 1.0 Channel Configuration.

    Attributes:
        f0: Fundamental frequency (16.384 kHz = 16384 Hz).
        num_channels: Number of channels (12).
        channels: List of channel definitions.
    """

    F0 = 16384.0  # 16.384 kHz

    # Channel table: (id, ratio a/b, label)
    _CHANNEL_DEFS = [
        (1, 1, 1, "CH1"),   # f0 itself — master clock
        (2, 2, 1, "CH2"),   # 2f0 — octave
        (3, 3, 2, "CH3"),   # 3/2 f0 — perfect fifth
        (4, 4, 3, "CH4"),   # 4/3 f0 — perfect fourth
        (5, 5, 4, "CH5"),   # 5/4 f0 — major third
        (6, 3, 1, "CH6"),   # 3f0 — fifth harmonic
        (7, 5, 3, "CH7"),   # 5/3 f0 — major sixth
        (8, 7, 4, "CH8"),   # 7/4 f0 — harmonic seventh
        (9, 7, 5, "CH9"),   # 7/5 f0 — tritone
        (10, 8, 5, "CH10"), # 8/5 f0 — minor sixth
        (11, 5, 2, "CH11"), # 5/2 f0 — major tenth
        (12, 7, 3, "CH12"), # 7/3 f0 — harmonic seventh
    ]

    def __init__(self):
        self.f0 = self.F0
        self.num_channels = len(self._CHANNEL_DEFS)
        self.channels = self._build_channels()

    def _build_channels(self) -> List[Dict]:
        """Build channel table with computed frequencies."""
        table = []
        for ch_id, a, b, label in self._CHANNEL_DEFS:
            ratio = f"{a}/{b}"
            frequency = (a / b) * self.f0
            table.append({
                "id": ch_id,
                "label": label,
                "a": a,
                "b": b,
                "ratio": ratio,
                "frequency_hz": frequency,
                "priority": 1.0 / (a + b),
            })
        return table

    def get_channel(self, channel_id: int) -> Dict:
        """Get a specific channel by ID (1-12)."""
        return self.channels[channel_id - 1]

    def frequency_range(self) -> tuple:
        """Return (min_freq, max_freq) across all channels."""
        freqs = [ch["frequency_hz"] for ch in self.channels]
        return (min(freqs), max(freqs))


def get_channel_table() -> List[Dict]:
    """Convenience function to get the HPM 1.0 channel table.

    Returns:
        List of 12 channel dicts.
    """
    config = HPM10Config()
    return config.channels


__all__ = ["HPM10Config", "get_channel_table"]
