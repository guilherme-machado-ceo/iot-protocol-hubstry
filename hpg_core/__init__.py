"""HPG — Harmonic Protocol Grid.

Grid generation, addressing, signal processing, and spectral verification.

Reference: DOI 10.5281/zenodo.19056387 (CC BY 4.0)
"""

from .omnigrid import compute_hn, cardinality_hn, omnigrid_2d
from .hpm_config import HPM10Config, get_channel_table
from .signal_processing import generate_composite_signal, decode_fft
from .spectral_verification import verify_rational_integrity, SpectralReport

__all__ = [
    "compute_hn",
    "cardinality_hn",
    "omnigrid_2d",
    "HPM10Config",
    "get_channel_table",
    "generate_composite_signal",
    "decode_fft",
    "verify_rational_integrity",
    "SpectralReport",
]
