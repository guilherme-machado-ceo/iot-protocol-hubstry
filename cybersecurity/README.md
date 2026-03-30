# Cybersecurity Framework — IoT Protocol Hubstry

> **Part of:** [Hubstry HALE Ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
> **Branch:** `cybersecurity-mvp` | **Version:** 2.0-MVP
> **Author:** Guilherme Gonçalves Machado — Hubstry Deep Tech, Rio de Janeiro, Brasil

---

## Strategic Context

This framework is built on two foundational innovations:

**HPG 1.0 — Harmonic Protocol Grid**
Multichannel IoT protocol based on rational harmonic subdivisions of f₀. Channels defined by irreducible fractions (a/b)·f₀ — 80 unique, spectrally separable channels for N=16.

**HALE — Harmonic Addressing & Labeling Equation**
General-purpose parent framework ([repo](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)). Any system derived from f₀ through sub-harmonic divisions f₀/n, where each sub-harmonic uniquely addresses a function in N-dimensional state space.

**Security Insight:** The harmonic structure is a **natural cryptographic primitive**. Phase coherence, spectral separability, and Euler's totient function provide structural guarantees directly usable for authentication, key derivation, and channel isolation.

---

## Architecture

```
╔══════════════════════════════════════════════════════════════╗
║        HALE ECOSYSTEM (hubstry-hale-ecosystem)               ║
║   f₀ → {f₀/n : n ∈ ℕ} → unique addresses → any system      ║
╠══════════════════════════════════════════════════════════════╣
║              IoT Protocol Hubstry (this repo)                ║
║   ℋ_N = {a/b · f₀ | gcd(a,b)=1, b≤N} → 80 channels        ║
╠══════════╦═══════════════╦══════════════╦════════════════════╣
║  HSL     ║  PQC Module   ║ Attack Guard ║  Compliance        ║
║ Harmonic ║ FIPS 203/204/ ║ OWASP Top 10 ║ ENISA NIS2        ║
║ Security ║ 205 (ML-KEM,  ║ ENISA 2025  ║ NIST CSF 2.0      ║
║ Layer    ║ ML-DSA,SLH-DSA║ 14 vectors  ║ ISO 27001:2022     ║
╚══════════╩═══════════════╩══════════════╩════════════════════╝
```

---

## Modules

| Module | Path | Description |
|---|---|---|
| HSL | [`hsl/`](./hsl/) | Harmonic Security Layer — phase-based authentication |
| Post-Quantum | [`post-quantum/`](./post-quantum/) | NIST FIPS 203/204/205 implementation roadmap |
| Attack Vectors | [`attack-vectors/`](./attack-vectors/) | 14 vectors with mitigations (ENISA 2025 + OWASP 2025) |
| Compliance | [`compliance/`](./compliance/) | ENISA NIS2, NIST CSF 2.0, ISO 27001, LGPD |

---

## Key Threat Intelligence (2025/2026)

### ENISA Threat Landscape 2025
*(4,875 incidents analyzed, July 2024 – June 2025)*
- **77%** of incidents: DDoS attacks
- **60%** of intrusions begin with phishing
- **#1 by damage:** Ransomware
- **Most impactful category:** Supply chain attacks
- **Emerging:** AI-augmented attacks

### NIST Post-Quantum Standards (August 2024)
- **FIPS 203** — ML-KEM (Kyber): key encapsulation
- **FIPS 204** — ML-DSA (Dilithium): digital signatures
- **FIPS 205** — SLH-DSA (SPHINCS+): hash-based backup
- **Migration deadline:** 2030 per NIST IR 8547

### OWASP Top 10 2025
1. Broken Access Control
2. Cryptographic Failures ← **PQC addresses this**
3. Injection (SQL, NoSQL, Command)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures ← **HSL addresses this**
8. Software Integrity Failures
9. Logging & Monitoring Failures
10. Server-Side Request Forgery

---

## HALE Framework Integration

| HALE Concept | HPG / Security Implementation |
|---|---|
| Fundamental state f₀ | Root key / base frequency |
| Sub-harmonics f₀/n | Channel addresses / hierarchical key space |
| Mapping function ψ | HSL phase auth / PQC key binding |
| N-dimensional state space | Multi-channel IoT topology |
| Euler's totient φ(b) | Sibling key count per hierarchy level |

👉 **Full framework:** [github.com/guilherme-machado-ceo/hubstry-hale-ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)

---

## Roadmap

| Milestone | Description | Target |
|---|---|---|
| MVP v2.0 | HSL design + PQC docs + attack vector coverage | Q1 2026 ✅ |
| v2.1 | Working HSL implementation (Python/C) | Q2 2026 |
| v2.2 | ML-KEM integration with HPG handshake | Q2 2026 |
| v2.3 | Threat detection / anomaly module | Q3 2026 |
| v3.0 | Hardware reference implementation | Q4 2026 |

---

## For Edital Submissions

Key differentiators for cybersecurity editais:
1. **Novel mathematical foundation** (HPG/HALE) — not a fork of existing tools
2. **Full NIST PQC alignment** — quantum-resistant by design
3. **IoT-native** — designed for constrained embedded systems
4. **International standards** — ENISA, NIST, ISO, OWASP
5. **Open source** — CC BY 4.0, auditable
6. **Brazilian authorship** — eligible for FINEP, BNDES, MCTI programs
