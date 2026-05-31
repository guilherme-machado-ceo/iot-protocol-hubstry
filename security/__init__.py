"""HPG-Sec — Security layer for the Harmonic Protocol Grid.

Includes HSL authentication, intrusion detection, and key rotation.

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from .hsl_auth import HSLAuth, HSLChallenge
from .intrusion_detection import IntrusionDetector, IntrusionReport
from .key_rotation import LFSRKeyRotation

__all__ = ["HSLAuth", "HSLChallenge", "IntrusionDetector", "IntrusionReport", "LFSRKeyRotation"]
