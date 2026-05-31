"""Intrusion detection via phase deviation analysis.

Monitors harmonic channels for unauthorized phase deviations
that indicate intrusion or signal tampering.

Detection rule: Δφ > ε triggers an alert.

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import pi
from typing import Dict, List, Optional, Tuple


@dataclass
class IntrusionReport:
    """Report from intrusion detection analysis.

    Attributes:
        total_channels: Number of channels monitored.
        alert_channels: Number of channels with detected deviations.
        severity: Severity level (none, low, medium, high, critical).
        alerts: List of individual channel alerts.
    """

    total_channels: int = 0
    alert_channels: int = 0
    severity: str = "none"
    alerts: List[Dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.severity == "none"


class IntrusionDetector:
    """Phase deviation intrusion detector.

    Continuously monitors harmonic channels for unexpected
    phase shifts that could indicate signal injection,
    eavesdropping, or man-in-the-middle attacks.

    Usage:
        detector = IntrusionDetector(threshold_rad=0.1)
        detector.register_channel("CH1", expected_phase=0.0)
        report = detector.check_phases({"CH1": 0.05})
    """

    def __init__(
        self,
        threshold_rad: float = 0.1,
        alert_threshold: int = 1,
    ):
        """Initialize detector.

        Args:
            threshold_rad: Phase deviation threshold ε in radians
                (default: 0.1 ≈ 5.7 degrees).
            alert_threshold: Number of alerts to escalate severity
                (default: 1 = any alert is high severity).
        """
        self.threshold_rad = threshold_rad
        self.alert_threshold = alert_threshold
        self._channels: Dict[str, float] = {}
        self._history: Dict[str, List[float]] = {}

    def register_channel(self, channel_id: str, expected_phase: float = 0.0):
        """Register a channel with its expected phase.

        Args:
            channel_id: Channel identifier (e.g., "CH1").
            expected_phase: Expected phase in radians (default: 0.0).
        """
        self._channels[channel_id] = expected_phase
        self._history[channel_id] = []

    def check_phases(
        self,
        observed_phases: Dict[str, float],
    ) -> IntrusionReport:
        """Check observed phases against expected values.

        Computes Δφ = |φ_observed - φ_expected| for each channel
        and flags any exceeding the threshold ε.

        Args:
            observed_phases: Dict mapping channel_id to observed phase.

        Returns:
            IntrusionReport with findings.
        """
        report = IntrusionReport(
            total_channels=len(self._channels),
        )

        for channel_id, expected_phase in self._channels.items():
            observed = observed_phases.get(channel_id, expected_phase)
            deviation = abs(observed - expected_phase)

            # Normalize to [-π, π]
            while deviation > pi:
                deviation -= 2 * pi

            # Record in history
            self._history[channel_id].append(deviation)

            # Check threshold
            if abs(deviation) > self.threshold_rad:
                report.alert_channels += 1
                report.alerts.append({
                    "channel_id": channel_id,
                    "expected_phase": expected_phase,
                    "observed_phase": observed,
                    "deviation_rad": float(deviation),
                    "deviation_deg": float(abs(deviation) * 180 / pi),
                    "threshold_rad": self.threshold_rad,
                })

        # Determine severity
        n_alerts = report.alert_channels
        if n_alerts == 0:
            report.severity = "none"
        elif n_alerts == 1:
            report.severity = "medium"
        elif n_alerts <= 3:
            report.severity = "high"
        else:
            report.severity = "critical"

        return report

    def get_channel_history(self, channel_id: str) -> List[float]:
        """Get deviation history for a channel."""
        return self._history.get(channel_id, [])


__all__ = ["IntrusionDetector", "IntrusionReport"]
