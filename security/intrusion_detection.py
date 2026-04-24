"""Intrusion Detection via Phase Deviation.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

Intrusion Detection Mechanism:
    Monitor the phase of each harmonic channel in the composite signal.
    If the observed phase deviates from the expected phase by more than
    a threshold epsilon, an intrusion is flagged:

        Delta_phi = |phi_observed - phi_expected| > epsilon

    Where:
        phi_observed = phase measured from the received signal
        phi_expected = phase computed from the known harmonic parameters
        epsilon = configurable detection threshold (radians)

This mechanism detects:
    - Signal injection: An attacker adding spurious harmonics
    - Signal substitution: An attacker replacing legitimate signals
    - Phase tampering: An attacker modifying the phase of channels
    - Replay attacks: Stale signals with mismatched phase evolution

The detection is based on the principle that legitimate harmonic
channels maintain phase coherence determined by their rational
frequency ratios, while injected or tampered signals exhibit
random phase deviations.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PhaseReading:
    """A phase measurement for a single channel.

    Attributes:
        channel_id: Channel identifier.
        observed_phase: Measured phase in radians.
        expected_phase: Expected phase in radians.
        timestamp: Unix timestamp of the measurement.
    """

    channel_id: int
    observed_phase: float
    expected_phase: float
    timestamp: float = 0.0

    @property
    def delta_phi(self) -> float:
        """Phase deviation |phi_observed - phi_expected|."""
        return abs(self.observed_phase - self.expected_phase)

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class IntrusionAlert:
    """Alert generated when intrusion is detected.

    Attributes:
        alert_id: Unique alert identifier.
        severity: Alert severity level.
        channel_id: Channel where intrusion was detected.
        delta_phi: Phase deviation in radians.
        threshold: Detection threshold in radians.
        timestamp: Unix timestamp of detection.
        description: Human-readable alert description.
    """

    alert_id: int
    severity: str
    channel_id: int
    delta_phi: float
    threshold: float
    timestamp: float
    description: str = ""


class PhaseMonitor:
    """Phase deviation intrusion detection monitor.

    Continuously monitors harmonic channels for phase deviations
    that exceed the configured threshold epsilon.

    Args:
        epsilon: Detection threshold in radians (default: 0.1 rad ~ 5.7 deg).
        window_size: Number of recent readings to track per channel.
        alert_callback: Optional callback function for alerts.
    """

    def __init__(
        self,
        epsilon: float = 0.1,
        window_size: int = 10,
        alert_callback: Optional[Any] = None,
    ) -> None:
        if epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {epsilon}")
        self.epsilon = epsilon
        self.window_size = window_size
        self.alert_callback = alert_callback
        self._readings: Dict[int, List[PhaseReading]] = {}
        self._alert_counter: int = 0
        self._total_checks: int = 0
        self._total_alerts: int = 0
        self._alert_history: List[IntrusionAlert] = []

    @property
    def stats(self) -> Dict[str, Any]:
        """Return monitoring statistics."""
        return {
            "epsilon_rad": self.epsilon,
            "epsilon_deg": math.degrees(self.epsilon),
            "total_checks": self._total_checks,
            "total_alerts": self._total_alerts,
            "alert_rate": (
                self._total_alerts / self._total_checks
                if self._total_checks > 0
                else 0.0
            ),
            "monitored_channels": list(self._readings.keys()),
        }

    def check_phase(
        self,
        channel_id: int,
        observed_phase: float,
        expected_phase: float,
    ) -> Optional[IntrusionAlert]:
        """Check a phase reading for intrusion.

        Computes Delta_phi = |phi_observed - phi_expected| and
        compares against the threshold epsilon.

        Args:
            channel_id: Channel being monitored.
            observed_phase: Measured phase in radians.
            expected_phase: Expected phase in radians.

        Returns:
            IntrusionAlert if deviation exceeds threshold, None otherwise.
        """
        self._total_checks += 1

        reading = PhaseReading(
            channel_id=channel_id,
            observed_phase=observed_phase,
            expected_phase=expected_phase,
        )

        if channel_id not in self._readings:
            self._readings[channel_id] = []
        self._readings[channel_id].append(reading)
        if len(self._readings[channel_id]) > self.window_size:
            self._readings[channel_id] = self._readings[channel_id][-self.window_size :]

        delta_phi = reading.delta_phi

        if delta_phi > self.epsilon:
            self._alert_counter += 1
            self._total_alerts += 1

            if delta_phi > self.epsilon * 3:
                severity = "CRITICAL"
            elif delta_phi > self.epsilon * 2:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            alert = IntrusionAlert(
                alert_id=self._alert_counter,
                severity=severity,
                channel_id=channel_id,
                delta_phi=delta_phi,
                threshold=self.epsilon,
                timestamp=time.time(),
                description=(
                    f"Phase deviation on CH{channel_id}: "
                    f"Delta_phi={delta_phi:.4f} rad "
                    f"({math.degrees(delta_phi):.2f} deg) "
                    f"> epsilon={self.epsilon:.4f} rad "
                    f"({math.degrees(self.epsilon):.2f} deg)"
                ),
            )
            self._alert_history.append(alert)
            if self.alert_callback:
                self.alert_callback(alert)
            return alert

        return None

    def check_channels(
        self,
        readings: List[Tuple[int, float, float]],
    ) -> List[IntrusionAlert]:
        """Check multiple channels simultaneously.

        Args:
            readings: List of (channel_id, observed_phase, expected_phase) tuples.

        Returns:
            List of IntrusionAlert for all triggered channels.
        """
        alerts: List[IntrusionAlert] = []
        for channel_id, obs, exp in readings:
            alert = self.check_phase(channel_id, obs, exp)
            if alert is not None:
                alerts.append(alert)
        return alerts

    def get_channel_history(self, channel_id: int) -> List[PhaseReading]:
        """Get the phase reading history for a channel.

        Args:
            channel_id: Channel identifier.

        Returns:
            List of recent PhaseReading objects.
        """
        return list(self._readings.get(channel_id, []))

    def get_alert_history(self, limit: int = 100) -> List[IntrusionAlert]:
        """Get recent alert history.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of recent IntrusionAlert objects.
        """
        return self._alert_history[-limit:]

    def reset(self) -> None:
        """Reset monitor state."""
        self._readings.clear()
        self._alert_counter = 0
        self._total_checks = 0
        self._total_alerts = 0
        self._alert_history.clear()


if __name__ == "__main__":
    print("=" * 60)
    print("Intrusion Detection - Example Usage")
    print("=" * 60)

    monitor = PhaseMonitor(epsilon=0.1)

    print(f"\nPhase deviation threshold: {monitor.epsilon} rad "
          f"({math.degrees(monitor.epsilon):.2f} deg)")

    print("\n--- Normal operation (no intrusion) ---")
    normal_readings = [
        (0, 0.001, 0.000),
        (1, 0.524, 0.524),
        (2, 1.047, 1.047),
        (3, 0.785, 0.785),
    ]
    alerts = monitor.check_channels(normal_readings)
    print(f"  Alerts: {len(alerts)} (expected 0)")

    print("\n--- Intrusion detected on CH2 ---")
    intrusion_readings = [
        (0, 0.002, 0.000),
        (1, 0.525, 0.524),
        (2, 1.847, 1.047),   # Delta_phi = 0.8 > 0.1
        (3, 0.786, 0.785),
    ]
    alerts = monitor.check_channels(intrusion_readings)
    for alert in alerts:
        print(f"  [{alert.severity}] {alert.description}")

    print("\n--- Multiple intrusions ---")
    multi_intrusion = [
        (4, 2.500, 1.571),  # Delta_phi = 0.929 > 0.1
        (5, 0.100, 0.000),  # Delta_phi = 0.1 = epsilon (not triggered)
        (6, 3.500, 3.142),  # Delta_phi = 0.358 > 0.1
    ]
    alerts = monitor.check_channels(multi_intrusion)
    for alert in alerts:
        print(f"  [{alert.severity}] {alert.description}")

    print("\n--- Monitoring statistics ---")
    stats = monitor.stats
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Alert rate: {stats['alert_rate']:.4f}")
    print(f"  Monitored channels: {stats['monitored_channels']}")

    print("\n--- Channel CH2 history ---")
    for reading in monitor.get_channel_history(2):
        print(f"  CH{reading.channel_id}: "
              f"obs={reading.observed_phase:.4f}, "
              f"exp={reading.expected_phase:.4f}, "
              f"delta={reading.delta_phi:.4f} rad")