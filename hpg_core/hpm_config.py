"""HPM 1.0 Channel Configuration.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

The HPM 1.0 (Harmonic Protocol Module) defines a practical channel
table with 12 channels selected from H_16, operating at a fundamental
frequency f0 = 16.384 kHz.

Channel Selection Criteria:
    - All ratios a/b satisfy gcd(a,b) = 1
    - All denominators b <= 6 for practical filter implementation
    - Ratios span both subharmonic (a < b) and superharmonic (a > b) regions
    - Priority ordering: P(a/b) = 1/(a+b), higher priority = lower a+b

Channel Table:
    CH0:  1/1  (16.384 kHz) - Control/pilot carrier
    CH1:  1/2  (8.192 kHz)  - Primary data
    CH2:  1/3  (5.461 kHz)  - Secondary data
    CH3:  2/3  (10.923 kHz) - Tertiary data
    CH4:  1/4  (4.096 kHz)  - Low-rate sensing
    CH5:  3/4  (12.288 kHz) - High-rate sensing
    CH6:  1/5  (3.277 kHz)  - Beacon/heartbeat
    CH7:  2/5  (6.554 kHz)  - Auxiliary control
    CH8:  3/5  (9.830 kHz)  - Telemetry
    CH9:  4/5  (13.107 kHz) - Status reporting
    CH10: 1/6  (2.731 kHz)  - Wake-up/alarm
    CH11: 5/6  (13.653 kHz) - Emergency
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HPMChannel:
    """A single channel in the HPM 1.0 table.

    Attributes:
        channel_id: Channel identifier (0-11).
        name: Human-readable channel name.
        a: Numerator of the harmonic ratio.
        b: Denominator of the harmonic ratio.
        description: Channel purpose description.
    """

    channel_id: int
    name: str
    a: int
    b: int
    description: str = ""

    @property
    def ratio_str(self) -> str:
        """Harmonic ratio as string a/b."""
        return f"{self.a}/{self.b}"

    @property
    def priority(self) -> float:
        """Channel priority P(a/b) = 1/(a+b)."""
        return 1.0 / (self.a + self.b)

    def frequency(self, f0: float) -> float:
        """Compute channel frequency: f = (a/b) * f0."""
        return (self.a / self.b) * f0

    def to_dict(self, f0: float) -> Dict[str, Any]:
        """Serialize channel to dictionary with computed frequency."""
        return {
            "id": self.channel_id,
            "name": self.name,
            "a": self.a,
            "b": self.b,
            "ratio": self.ratio_str,
            "frequency_hz": self.frequency(f0),
            "priority": self.priority,
            "description": self.description,
        }


@dataclass
class HPM10Config:
    """HPM 1.0 Protocol Configuration.

    Defines the complete HPM 1.0 operational parameters including
    the fundamental frequency, channel table, and protocol constants.

    Attributes:
        f0: Fundamental frequency in Hz (16.384 kHz).
        version: HPM protocol version string.
        num_channels: Number of defined channels (12).
    """

    f0: float = 16384.0
    version: str = "1.0"
    num_channels: int = 12
    _channels: List[HPMChannel] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._channels = [
            HPMChannel(0, "PILOT", 1, 1, "Control/pilot carrier"),
            HPMChannel(1, "DATA_PRI", 1, 2, "Primary data channel"),
            HPMChannel(2, "DATA_SEC", 1, 3, "Secondary data channel"),
            HPMChannel(3, "DATA_TER", 2, 3, "Tertiary data channel"),
            HPMChannel(4, "SENSE_LO", 1, 4, "Low-rate sensing"),
            HPMChannel(5, "SENSE_HI", 3, 4, "High-rate sensing"),
            HPMChannel(6, "BEACON", 1, 5, "Beacon/heartbeat"),
            HPMChannel(7, "AUX_CTRL", 2, 5, "Auxiliary control"),
            HPMChannel(8, "TELEMETRY", 3, 5, "Telemetry"),
            HPMChannel(9, "STATUS", 4, 5, "Status reporting"),
            HPMChannel(10, "WAKEUP", 1, 6, "Wake-up/alarm"),
            HPMChannel(11, "EMERGENCY", 5, 6, "Emergency channel"),
        ]

    @property
    def channels(self) -> List[HPMChannel]:
        """Return the list of defined HPM channels."""
        return list(self._channels)

    def get_channel(self, channel_id: int) -> Optional[HPMChannel]:
        """Get a channel by its ID.

        Args:
            channel_id: Channel identifier (0-11).

        Returns:
            HPMChannel if found, None otherwise.
        """
        for ch in self._channels:
            if ch.channel_id == channel_id:
                return ch
        return None

    def get_channel_table(self) -> List[Dict[str, Any]]:
        """Return the full channel table as a list of dictionaries.

        Returns:
            List of channel dictionaries with frequencies and priorities.
        """
        return [ch.to_dict(self.f0) for ch in self._channels]

    def get_frequencies(self) -> List[float]:
        """Return sorted list of channel frequencies in Hz."""
        freqs = [ch.frequency(self.f0) for ch in self._channels]
        return sorted(freqs)

    def get_resync_period(self) -> float:
        """Compute the natural re-synchronization period.

        T_sync = lcm(b1, b2, ..., bn) / f0

        For HPM 1.0 with denominators [1,2,3,4,5,6]:
        lcm(1,2,3,4,5,6) = 60
        T_sync = 60 / 16384 = 0.003662 s
        """
        denominators = list(set(ch.b for ch in self._channels))
        l = denominators[0]
        for b in denominators[1:]:
            l = (l * b) // math.gcd(l, b)
        return l / self.f0

    def get_config_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return {
            "version": self.version,
            "f0_hz": self.f0,
            "f0_khz": self.f0 / 1000.0,
            "num_channels": self.num_channels,
            "resync_period_s": self.get_resync_period(),
            "channels": self.get_channel_table(),
        }


def get_channel_table(f0: float = 16384.0) -> List[Dict[str, Any]]:
    """Convenience function to get the HPM 1.0 channel table.

    Args:
        f0: Fundamental frequency in Hz (default: 16384.0).

    Returns:
        List of channel dictionaries.
    """
    config = HPM10Config(f0=f0)
    return config.get_channel_table()


if __name__ == "__main__":
    print("=" * 60)
    print("HPM 1.0 Channel Configuration - Example Usage")
    print("=" * 60)

    config = HPM10Config()
    full_config = config.get_config_dict()

    print(f"\nHPM {full_config['version']} Configuration")
    print(f"  f0 = {full_config['f0_hz']} Hz ({full_config['f0_khz']} kHz)")
    print(f"  Channels: {full_config['num_channels']}")
    print(f"  T_sync = {full_config['resync_period_s']:.6f} s")

    print("\nChannel Table:")
    print(f"  {'ID':>3s} {'Name':>10s} {'Ratio':>5s} {'Freq (Hz)':>12s} "
          f"{'Priority':>10s}  Description")
    print("  " + "-" * 70)
    for ch in full_config["channels"]:
        print(
            f"  {ch['id']:3d} {ch['name']:>10s} {ch['ratio']:>5s} "
            f"{ch['frequency_hz']:12.3f} {ch['priority']:10.6f}  "
            f"{ch['description']}"
        )

    print("\nFrequencies (sorted):")
    for f in config.get_frequencies():
        print(f"  {f:12.3f} Hz")

    print("\nResynchronization period:")
    print(f"  T_sync = {config.get_resync_period():.6f} s "
          f"({1.0/config.get_resync_period():.1f} Hz)")