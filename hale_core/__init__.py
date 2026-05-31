"""HALE — Harmonic Addressing & Labeling Equation.

Core pipeline: f0 → H → h → ψ → c → M → g

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from .hale_equation import HALEPipeline
from .psi_functions import psi1, psi2, psi3, psi4

__all__ = ["HALEPipeline", "psi1", "psi2", "psi3", "psi4"]
