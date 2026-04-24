"""LFSR Key Rotation.

Based on HPG 1.0 (CC BY 4.0):
    DOI: 10.5281/zenodo.19056387 - HPG 1.0 Harmonic Protocol Grid

LFSR (Linear Feedback Shift Register) Key Rotation:
    Uses a Galois LFSR to generate a pseudo-random sequence of
    session keys. The LFSR is seeded from the fundamental frequency
    f0 combined with a timestamp, ensuring unique key sequences
    per time interval.

Seed Generation:
    seed = hash(f0 || timestamp) mod 2^register_size

LFSR Operation (Galois configuration):
    For each clock cycle:
        1. Extract the LSB (output bit)
        2. If LSB == 1: state ^= feedback_polynomial
        3. Shift state right by 1 bit
        4. Insert feedback bit at MSB

Feedback Polynomials (standard):
    16-bit: x^16 + x^14 + x^13 + x^11 + 1  (taps: [16,14,13,11])
    32-bit: x^32 + x^22 + x^2 + x^1 + 1     (taps: [32,22,2,1])

Key Derivation:
    Each key is derived by hashing the current LFSR state
    combined with a counter and the original seed material.

Properties:
    - Maximum period: 2^n - 1 for a primitive polynomial
    - Deterministic: Same seed produces same sequence
    - Efficient: O(1) per key generation (single XOR + shift)
    - Stateless: Key derivation does not require storing history
"""

from __future__ import annotations

import hashlib
import struct
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


# Standard feedback polynomials for Galois LFSR
LFSR_POLYNOMIALS: Dict[int, int] = {
    8: 0xB8,       # x^8 + x^6 + x^5 + x^4 + 1
    16: 0xD800,    # x^16 + x^14 + x^13 + x^11 + 1
    32: 0x8040003, # x^32 + x^22 + x^2 + x^1 + 1
    64: 0xD800000000000000,  # x^64 + x^62 + x^60 + x^59 + 1
}


@dataclass
class LFSRKeyRotator:
    """LFSR-based key rotation engine.

    Generates a deterministic sequence of cryptographic keys using
    a Galois LFSR seeded from f0 and timestamp.

    Args:
        f0: Fundamental frequency (used as seed material).
        register_size: LFSR register size in bits (8, 16, 32, or 64).
        polynomial: Optional custom feedback polynomial. If None,
                    uses the standard polynomial for the register size.
        key_length: Output key length in bytes (default: 32).
    """

    f0: float
    register_size: int = 32
    polynomial: Optional[int] = None
    key_length: int = 32
    _state: int = 0
    _counter: int = 0
    _seed_value: int = 0

    def __post_init__(self) -> None:
        if self.register_size not in LFSR_POLYNOMIALS:
            valid = ", ".join(str(k) for k in sorted(LFSR_POLYNOMIALS.keys()))
            raise ValueError(
                f"register_size must be one of {valid}, "
                f"got {self.register_size}"
            )
        if self.polynomial is None:
            self.polynomial = LFSR_POLYNOMIALS[self.register_size]
        max_state = (1 << self.register_size) - 1
        mask = max_state

        seed_input = f"{self.f0}:{time.time()}:{self.register_size}"
        seed_hash = hashlib.sha256(seed_input.encode()).digest()
        self._seed_value = int.from_bytes(seed_hash[:8], "big") & mask
        self._state = self._seed_value
        if self._state == 0:
            self._state = 1

    @property
    def state(self) -> int:
        """Current LFSR state."""
        return self._state

    @property
    def counter(self) -> int:
        """Number of keys generated so far."""
        return self._counter

    @property
    def max_period(self) -> int:
        """Maximum LFSR period (2^n - 1)."""
        return (1 << self.register_size) - 1

    def _lfsr_step(self) -> int:
        """Perform one LFSR clock cycle (Galois configuration).

        Returns:
            The output bit (LSB before shift).
        """
        mask = (1 << self.register_size) - 1
        output_bit = self._state & 1
        if output_bit:
            self._state ^= self.polynomial
        self._state = (self._state >> 1) | (output_bit << (self.register_size - 1))
        self._state &= mask
        return output_bit

    def _derive_key(self, state: int, counter: int) -> bytes:
        """Derive a cryptographic key from LFSR state and counter.

        Args:
            state: Current LFSR state.
            counter: Key generation counter.

        Returns:
            Derived key bytes of configured length.
        """
        data = struct.pack(
            f">QQ{self.key_length}s",
            state,
            counter,
            self._seed_value.to_bytes(self.key_length, "big")[: self.key_length],
        )
        h = hashlib.sha256(data).digest()
        if len(h) > self.key_length:
            h = h[: self.key_length]
        return h

    def rotate(self, steps: int = 1) -> bytes:
        """Generate the next key by advancing the LFSR.

        Args:
            steps: Number of LFSR steps to advance (default: 1).

        Returns:
            Derived key bytes.
        """
        for _ in range(steps):
            self._lfsr_step()
            self._counter += 1
        return self._derive_key(self._state, self._counter)

    def rotate_to(self, target_counter: int) -> bytes:
        """Advance to a specific counter value and return the key.

        Args:
            target_counter: Target counter value.

        Returns:
            Derived key at the target counter.
        """
        steps = target_counter - self._counter
        if steps > 0:
            return self.rotate(steps)
        return self._derive_key(self._state, self._counter)

    def generate_key_sequence(
        self, count: int, steps_between: int = 1
    ) -> List[bytes]:
        """Generate a sequence of keys.

        Args:
            count: Number of keys to generate.
            steps_between: LFSR steps between consecutive keys.

        Returns:
            List of key bytes.
        """
        keys: List[bytes] = []
        for i in range(count):
            keys.append(self.rotate(steps_between))
        return keys

    def reset(self, timestamp: Optional[float] = None) -> None:
        """Reset the LFSR with a new seed.

        Args:
            timestamp: Optional timestamp for seed. If None, uses current time.
        """
        ts = timestamp if timestamp is not None else time.time()
        mask = (1 << self.register_size) - 1
        seed_input = f"{self.f0}:{ts}:{self.register_size}"
        seed_hash = hashlib.sha256(seed_input.encode()).digest()
        self._seed_value = int.from_bytes(seed_hash[:8], "big") & mask
        self._state = self._seed_value
        if self._state == 0:
            self._state = 1
        self._counter = 0

    def get_info(self) -> Dict[str, Any]:
        """Return rotator configuration and state information."""
        return {
            "f0": self.f0,
            "register_size_bits": self.register_size,
            "polynomial_hex": hex(self.polynomial),
            "key_length_bytes": self.key_length,
            "max_period": self.max_period,
            "current_state": hex(self._state),
            "counter": self._counter,
            "period_progress": self._counter / self.max_period,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("LFSR Key Rotation - Example Usage")
    print("=" * 60)

    f0 = 16384.0

    # Example 1: Basic 16-bit LFSR
    print("\n--- 16-bit LFSR ---")
    rot16 = LFSRKeyRotator(f0=f0, register_size=16, key_length=16)
    print(f"State: {hex(rot16.state)}")
    print(f"Polynomial: {hex(rot16.polynomial)}")
    print(f"Max period: {rot16.max_period}")

    keys = rot16.generate_key_sequence(5)
    for i, key in enumerate(keys):
        print(f"  Key {i+1}: {key.hex()}")

    # Example 2: 32-bit LFSR
    print("\n--- 32-bit LFSR ---")
    rot32 = LFSRKeyRotator(f0=f0, register_size=32, key_length=32)
    info = rot32.get_info()
    print(f"State: {info['current_state']}")
    print(f"Polynomial: {info['polynomial_hex']}")
    print(f"Max period: {info['max_period']}")

    keys32 = rot32.generate_key_sequence(5)
    for i, key in enumerate(keys32):
        print(f"  Key {i+1}: {key.hex()}")

    # Example 3: Period verification
    print("\n--- Period verification (8-bit LFSR) ---")
    rot8 = LFSRKeyRotator(f0=f0, register_size=8, key_length=8)
    original_state = rot8.state
    period_found = 0

    for i in range(rot8.max_period + 10):
        rot8.rotate()
        if rot8.state == original_state:
            period_found = i + 1
            break

    print(f"  Expected max period: {rot8.max_period}")
    print(f"  Actual period found: {period_found}")
    print(f"  Match: {period_found == rot8.max_period}")

    # Example 4: Key uniqueness
    print("\n--- Key uniqueness check ---")
    rot_unique = LFSRKeyRotator(f0=f0, register_size=32, key_length=32)
    unique_keys = set()
    num_keys = 1000
    for _ in range(num_keys):
        key = rot_unique.rotate()
        unique_keys.add(key.hex())
    print(f"  Generated: {num_keys} keys")
    print(f"  Unique: {len(unique_keys)} keys")
    print(f"  Collisions: {num_keys - len(unique_keys)}")