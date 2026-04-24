"""HALE Core - Harmonic Addressing Pipeline.

THEORETICAL REFERENCE (CC BY-NC-ND 4.0 - NO CODE DERIVATIVES):
  DOI: 10.5281/zenodo.18901934 - HALE Working Paper v3.0

IMPLEMENTATION BASED ON (CC BY 4.0):
  DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid
"""

from hale_core.hale_equation import HALEPipeline, HarmonicVector, ChannelAddress
from hale_core.psi_functions import psi1_direct, psi2_binary, psi3_prime, psi4_learned

__all__ = [
    "HALEPipeline",
    "HarmonicVector",
    "ChannelAddress",
    "psi1_direct",
    "psi2_binary",
    "psi3_prime",
    "psi4_learned",
]