"""Security Layer - HSL Authentication, Intrusion Detection, Key Rotation.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

Security features:
    - H-Challenge/Response 3-step authentication protocol
    - Phase deviation intrusion detection (Delta_phi > epsilon)
    - LFSR key rotation with seed from f0 + timestamp
"""

from security.hsl_auth import HSLAuthEngine, AuthChallenge, AuthResponse, AuthResult
from security.intrusion_detection import PhaseMonitor, IntrusionAlert
from security.key_rotation import LFSRKeyRotator

__all__ = [
    "HSLAuthEngine",
    "AuthChallenge",
    "AuthResponse",
    "AuthResult",
    "PhaseMonitor",
    "IntrusionAlert",
    "LFSRKeyRotator",
]