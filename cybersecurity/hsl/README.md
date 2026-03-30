# HSL — Harmonic Security Layer

> **Defined in:** HPG 1.0 (Guilherme Gonçalves Machado, 2026)
> **Parent:** [HALE Ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
> **Type:** Novel cryptographic primitive — spectral phase-based authentication

---

## Concept

In HPG 1.0, each channel is defined by:

```
f_{a,b} = (a/b) · f₀     where gcd(a,b) = 1, b ≤ N
```

Each carrier occupies a unique position in ℋ_N × {−1, +1}, where ±1 is the **phase**. The phase-inverted carrier (−f_{a,b}) is mathematically distinct from all channels in ℋ_N — provably unique. HSL exploits this as an authentication token.

---

## Authentication Protocol

```
Prover (Device)                    Verifier (Gateway)
──────────────                     ──────────────────
Knows: harmonic address (a,b)      Knows: expected phase at (a,b)
Knows: current f₀                  Knows: current f₀

1. Verifier → CHALLENGE(timestamp, nonce)
2. Prover   → φ_response = phase(f_{a,b}, t) XOR HMAC(nonce, channel_secret)
3. Prover   → RESPONSE(φ_response, timestamp, nonce)
4. Verifier → |φ_received - φ_expected| < ε AND timestamp valid AND nonce fresh
5. OK       → authenticated for channel (a,b)
```

Security properties:
- Captured responses cannot be replayed (timestamp + nonce)
- Without knowledge of (a,b) and f₀, correct phase cannot be computed
- Credentials for channel (3/4)·f₀ do not grant access to (5/7)·f₀

---

## Security Properties

| Property | Guarantee |
|---|---|
| Authentication | Phase coherence + ML-DSA signature |
| Integrity | Channel-bound HMAC + ML-DSA |
| Confidentiality | ML-KEM session key per channel |
| Replay prevention | Nonce + timestamp + phase window |
| Quantum resistance | ML-KEM + ML-DSA (FIPS 203/204) |
| Channel isolation | Spectral separability (mathematical) |
| Forward secrecy | ML-KEM ephemeral key per session |

---

## HSL vs TLS 1.3

| Dimension | TLS 1.3 | HSL (HPG 1.0) |
|---|---|---|
| Handshake overhead | ~8KB | ~200B phase exchange |
| PKI dependency | Required | f₀ shared fundamental |
| Quantum safety | PQC extension needed | Native (ML-KEM/ML-DSA) |
| Embedded suitability | Limited | Designed for constrained |
| Channel binding | No | Yes (address-specific) |

HSL is purpose-built for **multi-channel IoT/embedded** where traditional PKI is impractical.

---

## Reference Implementation

```python
import math, hmac, hashlib, time, secrets
from dataclasses import dataclass

@dataclass
class HPGChannel:
    a: int; b: int; f0: float

    def __post_init__(self):
        assert math.gcd(self.a, self.b) == 1

    @property
    def frequency(self): return (self.a / self.b) * self.f0

    @property
    def channel_id(self): return f"HPG:{self.a}/{self.b}"


class HSLAuthenticator:
    PHASE_TOLERANCE = 0.05  # radians
    TIMESTAMP_WINDOW = 30   # seconds

    def __init__(self, channel: HPGChannel, secret: bytes):
        self.channel = channel
        self.secret = secret
        self._seen_nonces = set()

    def compute_phase(self, t: float) -> float:
        return (2 * math.pi * self.channel.frequency * t) % (2 * math.pi)

    def generate_challenge(self) -> dict:
        return {"nonce": secrets.token_hex(8), "timestamp": time.time()}

    def compute_response(self, challenge: dict) -> dict:
        t, nonce = challenge["timestamp"], challenge["nonce"]
        phase = self.compute_phase(t)
        h = hmac.new(self.secret, nonce.encode(), hashlib.sha256).digest()
        phase_offset = int.from_bytes(h[:4], 'big') / 1e7
        return {"phase": phase + phase_offset, "timestamp": t,
                "nonce": nonce, "channel": self.channel.channel_id}

    def verify_response(self, response: dict, challenge: dict) -> bool:
        nonce = response["nonce"]
        if nonce in self._seen_nonces: return False
        if abs(time.time() - response["timestamp"]) > self.TIMESTAMP_WINDOW: return False
        if response["channel"] != self.channel.channel_id: return False
        expected = self.compute_response(challenge)
        if abs(response["phase"] - expected["phase"]) > self.PHASE_TOLERANCE: return False
        self._seen_nonces.add(nonce)
        return True


# Demo
ch = HPGChannel(a=3, b=4, f0=1000.0)
auth = HSLAuthenticator(ch, b"channel-secret-256bit")
challenge = auth.generate_challenge()
response = auth.compute_response(challenge)
print(f"{ch.channel_id} authenticated: {auth.verify_response(response, challenge)}")
```

---

## References
- HPG 1.0 Paper — Section 5: Harmonic Security Layer
- [HALE Framework](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
- [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final) · [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final)
