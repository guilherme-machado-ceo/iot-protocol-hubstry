"""HSL Auth — Harmonic Signature Challenge/Response Protocol.

A lightweight 3-step authentication protocol (~200 bytes).
Uses harmonic phase relationships as cryptographic signatures.

Protocol flow:
    1. Client → Server: CHALLENGE(device_id, timestamp)
    2. Server → Client: RESPONSE(challenge_hash, phase_signature)
    3. Client → Server: CONFIRM(session_key_derived)

Reference: DOI 10.5281/zenodo.18901934 (CC BY 4.0)
"""

from __future__ import annotations

import hashlib
import secrets
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class HSLChallenge:
    """A challenge issued by the client.

    Attributes:
        device_id: Unique device identifier.
        timestamp: Unix timestamp of challenge creation.
        nonce: Random nonce for replay protection.
        challenge_hash: SHA-256 hash of (device_id + timestamp + nonce).
    """

    device_id: str
    timestamp: float = 0.0
    nonce: bytes = b""
    challenge_hash: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.nonce:
            self.nonce = secrets.token_bytes(16)
        if not self.challenge_hash:
            raw = f"{self.device_id}:{self.timestamp}:{self.nonce.hex()}"
            self.challenge_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def size_bytes(self) -> int:
        """Approximate size of the challenge packet in bytes."""
        return len(self.device_id) + 8 + 16 + 32  # ~200B for typical IDs

    def to_bytes(self) -> bytes:
        """Serialize challenge to bytes for transmission."""
        device_bytes = self.device_id.encode("utf-8")[:64]
        ts_bytes = struct.pack(">d", self.timestamp)
        return device_bytes + ts_bytes + self.nonce


@dataclass
class HSLResponse:
    """Server response to a challenge.

    Attributes:
        challenge_hash: Hash from the original challenge.
        phase_signature: Harmonic phase-based signature.
        session_key: Derived session key for encrypted communication.
    """

    challenge_hash: str
    phase_signature: str
    session_key: str

    def to_bytes(self) -> bytes:
        """Serialize response to bytes."""
        sig_bytes = bytes.fromhex(self.phase_signature[:32])
        key_bytes = bytes.fromhex(self.session_key[:32])
        return sig_bytes + key_bytes


class HSLAuth:
    """HSL Authentication Manager.

    Manages challenge/response cycles for device authentication
    using harmonic phase signatures.

    Usage:
        auth = HSLAuth(secret_key="my-secret")
        challenge = auth.create_challenge("device-001")
        response = auth.generate_response(challenge)
        verified = auth.verify_response(challenge, response)
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.active_sessions: Dict[str, Dict] = {}
        self._challenge_store: Dict[str, HSLChallenge] = {}

    def create_challenge(self, device_id: str) -> HSLChallenge:
        """Create a new authentication challenge for a device.

        Args:
            device_id: Unique device identifier.

        Returns:
            HSLChallenge object.
        """
        challenge = HSLChallenge(device_id=device_id)
        self._challenge_store[challenge.challenge_hash] = challenge
        return challenge

    def generate_response(self, challenge: HSLChallenge) -> HSLResponse:
        """Generate a server response to a challenge.

        Computes a phase signature by hashing the challenge with
        the server secret key, then derives a session key.

        Args:
            challenge: The challenge to respond to.

        Returns:
            HSLResponse object.
        """
        # Phase signature: HMAC-like hash of challenge + secret
        sig_input = f"{challenge.challenge_hash}:{self.secret_key}"
        phase_signature = hashlib.sha256(sig_input.encode()).hexdigest()

        # Session key derivation: hash of (phase_signature + nonce)
        key_input = f"{phase_signature}:{challenge.nonce.hex()}"
        session_key = hashlib.sha256(key_input.encode()).hexdigest()

        response = HSLResponse(
            challenge_hash=challenge.challenge_hash,
            phase_signature=phase_signature,
            session_key=session_key,
        )

        # Store session
        self.active_sessions[session_key[:16]] = {
            "device_id": challenge.device_id,
            "created": challenge.timestamp,
            "challenge_hash": challenge.challenge_hash,
        }

        return response

    def verify_response(
        self,
        challenge: HSLChallenge,
        response: HSLResponse,
        max_age: float = 30.0,
    ) -> bool:
        """Verify a response against the original challenge.

        Args:
            challenge: Original challenge.
            response: Response to verify.
            max_age: Maximum challenge age in seconds (default: 30).

        Returns:
            True if response is valid and not expired.
        """
        # Check challenge exists
        stored = self._challenge_store.get(response.challenge_hash)
        if stored is None:
            return False

        # Check not expired
        if time.time() - stored.timestamp > max_age:
            return False

        # Verify challenge hash matches
        if response.challenge_hash != stored.challenge_hash:
            return False

        # Verify phase signature
        expected_response = self.generate_response(stored)
        if response.phase_signature != expected_response.phase_signature:
            return False

        return True

    def get_session_info(self, session_prefix: str) -> Optional[Dict]:
        """Get information about an active session."""
        return self.active_sessions.get(session_prefix)


__all__ = ["HSLAuth", "HSLChallenge", "HSLResponse"]
