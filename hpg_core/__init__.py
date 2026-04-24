"""HPG Core - Harmonic Protocol Grid.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid
"""

from hpg_core.omnigrid import compute_hn, cardinality_hn, omnigrid_2d, euler_totient
from hpg_core.hpm_config import HPM10Config, get_channel_table
from hpg_core.signal_processing import generate_composite_signal, decode_fft
from hpg_core.spectral_verification import verify_rational_ratio, verify_grid_integrity

__all__ = [
    "compute_hn",
    "cardinality_hn",
    "omnigrid_2d",
    "euler_totient",
    "HPM10Config",
    "get_channel_table",
    "generate_composite_signal",
    "decode_fft",
    "verify_rational_ratio",
    "verify_grid_integrity",
]