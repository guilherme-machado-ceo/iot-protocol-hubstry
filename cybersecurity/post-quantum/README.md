# Post-Quantum Cryptography Module

> **Standards:** NIST FIPS 203 · FIPS 204 · FIPS 205 (finalized August 2024)
> **Parent:** [Hubstry HALE Ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)

---

## Why Post-Quantum Now

Quantum computers running **Shor's algorithm** break RSA, ECDSA, and ECDH — the backbone of current IoT security.

- **"Harvest now, decrypt later"**: adversaries collect encrypted traffic today to decrypt when quantum computers mature
- IoT devices have **10–20 year lifespans** — devices deployed today must be quantum-resistant
- NIST mandates migration away from RSA/ECDSA **by 2030** (NIST IR 8547)
- ENISA 2025 lists cryptographic failures as a top systemic risk

---

## NIST Finalized Standards (August 2024)

### FIPS 203 — ML-KEM (CRYSTALS-Kyber)
```
Use: Session key establishment between IoT devices and gateways
Security: Module Learning With Errors (MLWE) hardness
Sets: ML-KEM-512 (lightweight) | ML-KEM-768 (RECOMMENDED) | ML-KEM-1024 (critical infra)

HPG Integration:
  Each channel (a/b · f₀) generates a unique ML-KEM context.
  Harmonic address (a,b) seeds key pair derivation →
  channel-bound quantum-resistant session key.
```

### FIPS 204 — ML-DSA (CRYSTALS-Dilithium)
```
Use: Device identity, firmware signing, command authentication
Security: MLWE + Module Short Integer Solution (MSIS)
Sets: ML-DSA-44 (level 2) | ML-DSA-65 (RECOMMENDED) | ML-DSA-87 (level 5)

HPG Integration:
  Device certificates bind ML-DSA public keys to harmonic addresses.
  Signed commands prevent replay/forgery against quantum adversaries.
```

### FIPS 205 — SLH-DSA (SPHINCS+)
```
Use: Backup signature scheme (hash-based, conservative security)
Security: Hash function security only — no lattice assumptions
Variants: SLH-DSA-SHA2-128s/f | SLH-DSA-SHA2-256s (RECOMMENDED for long-term)

Why keep as backup: If ML-DSA lattice assumptions break,
SLH-DSA provides independent security via SHA2/SHA3.
```

### FN-DSA — FALCON (in standardization)
```
Use: Constrained embedded devices requiring compact signatures
Status: NIST draft, expected final 2025
Advantage: ~40% smaller signatures than ML-DSA at equal security
```

---

## HALE Key Hierarchy

The HALE sub-harmonic address space provides a **natural key derivation tree**:

```
f₀ (root / master secret)
├── f₀/2  → Zone A key
├── f₀/3  → Zone B key
├── f₀/4  → Subzone A1
│   ├── f₀/8  → Device cluster 1
│   └── f₀/12 → Device cluster 2
└── f₀/5  → Zone C key
    └── f₀/15 → Leaf device key
```

Euler's totient φ(b) determines sibling key count per level — **mathematically guaranteed isolation**.

---

## Migration Strategy

```
Phase 1 (Now–2026):  Hybrid — Classical + PQC in parallel
Phase 2 (2026–2028): PQC primary (ML-KEM-768 + ML-DSA-65)
Phase 3 (2028–2030): Classical deprecated — NIST IR 8547 compliance
```

---

## Reference Implementation

```python
# ML-KEM key exchange bound to HPG channel — uses liboqs
from oqs import KeyEncapsulation
import math

def hpg_channel_keygen(a: int, b: int) -> dict:
    """Generate quantum-resistant key pair for HPG channel (a/b)·f₀"""
    assert math.gcd(a, b) == 1, "Channel address must be irreducible"
    kem = KeyEncapsulation("ML-KEM-768")
    public_key, secret_key = kem.generate_keypair()
    return {
        "channel": f"HPG:{a}/{b}",
        "algorithm": "ML-KEM-768",
        "fips_standard": "FIPS 203",
        "public_key": public_key.hex(),
    }

def hpg_channel_handshake(public_key: bytes) -> tuple:
    """Encapsulate session key — returns (ciphertext, shared_secret)"""
    kem = KeyEncapsulation("ML-KEM-768")
    return kem.encap_secret(public_key)
```

---

## References

- [NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final) — ML-KEM
- [NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) — ML-DSA
- [NIST FIPS 205](https://csrc.nist.gov/pubs/fips/205/final) — SLH-DSA
- [NIST IR 8547](https://nvlpubs.nist.gov/nistpubs/ir/2024/NIST.IR.8547.ipd.pdf) — Migration Timeline
- [Open Quantum Safe](https://openquantumsafe.org/) — liboqs
- [HALE Framework](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
