"""LFSR Key Rotation Engine.

Implements a Linear Feedback Shift Register for cryptographic
key rotation. Used to periodically update session keys
in the HPG-Sec security layer.

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from __future__ import annotations

import hashlib
from typing import List, Optional


class LFSRKeyRotation:
    """LFSR-based key rotation engine.

    Generates a sequence of cryptographic keys using an LFSR
    with configurable polynomial taps. Each key is derived
    by hashing the LFSR state.

    Usage:
        lfsr = LFSRKeyRotation(seed=0xDEADBEEF, register_size=16)
        key1 = lfsr.next_key()
        key2 = lfsr.next_key()
        lfsr.reset()
    """

    # Common LFSR tap polynomials (maximum-length sequences)
    TAP_POLYNOMIALS = {
        8: [7, 5, 4, 3],       # x^8 + x^7 + x^5 + x^4 + x^3 + 1
        16: [15, 13, 12, 10],   # x^16 + x^15 + x^13 + x^12 + x^10 + 1
        32: [31, 21, 13, 7],    # x^32 + x^31 + x^21 + x^13 + x^7 + 1
    }

    def __init__(
        self,
        seed: int = 0xDEADBEEF,
        register_size: int = 16,
        taps: Optional[List[int]] = None,
    ):
        """Initialize LFSR.

        Args:
            seed: Initial seed value (integer).
            register_size: Size of the LFSR register in bits (8, 16, or 32).
            taps: Feedback tap positions. If None, uses default polynomial.
        """
        if register_size not in self.TAP_POLYNOMIALS and taps is None:
            raise ValueError(
                f"Register size {register_size} not supported. "
                f"Use {list(self.TAP_POLYNOMIALS.keys())} or provide custom taps."
            )

        self.register_size = register_size
        self.taps = taps or self.TAP_POLYNOMIALS[register_size]
        self.mask = (1 << register_size) - 1
        self.state = seed & self.mask
        self.initial_seed = self.state
        self.generation_count = 0
        self._key_cache: List[str] = []

    def _step(self) -> int:
        """Advance the LFSR by one step.

        XORs the bits at tap positions and feeds the result
        back into the register.

        Returns:
            New register state.
        """
        feedback = 0
        for tap in self.taps:
            feedback ^= (self.state >> tap) & 1
        self.state = ((self.state << 1) | feedback) & self.mask
        return self.state

    def next_key(self) -> str:
        """Generate the next key in the rotation sequence.

        Advances the LFSR and derives a key by hashing the state.

        Returns:
            Hexadecimal key string (64 chars = 256 bits).
        """
        self._step()
        self.generation_count += 1
        raw = f"lfsr:{self.state}:{self.generation_count}:{self.register_size}"
        key = hashlib.sha256(raw.encode()).hexdigest()
        self._key_cache.append(key)
        return key

    def next_keys(self, count: int) -> List[str]:
        """Generate multiple keys at once.

        Args:
            count: Number of keys to generate.

        Returns:
            List of hexadecimal key strings.
        """
        return [self.next_key() for _ in range(count)]

    def reset(self):
        """Reset LFSR to initial seed state."""
        self.state = self.initial_seed
        self.generation_count = 0
        self._key_cache = []

    @property
    def period(self) -> int:
        """Maximum period of the LFSR (2^n - 1 for maximal-length)."""
        return (1 << self.register_size) - 1

    @property
    def key_index(self) -> int:
        """Current key generation index (0-based)."""
        return self.generation_count - 1

    def get_history(self) -> List[str]:
        """Get all previously generated keys."""
        return self._key_cache.copy()


__all__ = ["LFSRKeyRotation"]
