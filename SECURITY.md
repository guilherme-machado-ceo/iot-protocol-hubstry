# Security Policy — IoT Protocol Hubstry

> **Parent Framework:** [Hubstry HALE Ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
> **Branch:** `cybersecurity-mvp`
> **Maintainer:** Guilherme Gonçalves Machado — Hubstry Deep Tech
> **Last updated:** March 2026
> **References:** ENISA Threat Landscape 2025 · NIST FIPS 203/204/205 · OWASP Top 10 2025

---

## Overview

This repository implements the **IoT Protocol Hubstry** security architecture, a sub-domain of the [HALE (Harmonic Addressing & Labeling Equation)](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem) framework. Security here is not an add-on layer — it is **structurally embedded** in the Harmonic Protocol Grid (HPG 1.0) via the **Harmonic Security Layer (HSL)**, a phase-coherence-based authentication mechanism derived from the mathematical properties of rational harmonic subdivisions.

---

## Supported Versions

| Version | Branch | Status |
|---|---|---|
| 1.x (IoT Core) | `master` | ✅ Supported |
| 2.0 (Cybersecurity MVP) | `cybersecurity-mvp` | 🚧 Active development |

---

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Report privately via [GitHub Security Advisory](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/security/advisories/new).
Response SLA: 72h acknowledgement, 30 days for patch.

---

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│    HALE Ecosystem (hubstry-hale-ecosystem)       │
│    f₀ → sub-harmonics → unique addresses         │
├─────────────────────────────────────────────────┤
│         IoT Protocol Hubstry (this repo)         │
│  HPG 1.0 + HSL (phase-based authentication)     │
├──────────────┬──────────────┬───────────────────┤
│  PQC Layer   │ Attack Guard │ Compliance Layer   │
│ ML-KEM/ML-DSA│ OWASP Top 10 │ ENISA · NIST · ISO │
└──────────────┴──────────────┴───────────────────┘
```

### HSL — Harmonic Security Layer
Each channel defined by irreducible fraction (a/b)·f₀. Phase inversion serves as spectral authentication token — unforgeable without knowledge of the harmonic address space.

---

## Post-Quantum Cryptography (PQC)

Per NIST August 2024 finalized standards:

| Standard | Algorithm | Use Case | Status |
|---|---|---|---|
| FIPS 203 | ML-KEM (Kyber-768) | Key encapsulation | ✅ Designed |
| FIPS 204 | ML-DSA (Dilithium-3) | Digital signatures | ✅ Designed |
| FIPS 205 | SLH-DSA (SPHINCS+) | Hash-based backup | 🔄 Roadmap |

Migration deadline: 2030 (NIST IR 8547). See: [`cybersecurity/post-quantum/`](./cybersecurity/post-quantum/)

---

## Attack Vector Coverage (ENISA 2025 + OWASP 2025)

| Vector | Prevalence | Coverage |
|---|---|---|
| DDoS | 77% of incidents | Channel isolation, rate limiting |
| Phishing | 60% intrusion vector | HSL auth, MFA, ML-DSA signing |
| SQL Injection | OWASP A05 | Parameterized queries, WAF |
| Brute Force | OWASP A07 | Rate limiting, HSL tokens |
| Supply Chain | Most impactful | SBOM, signed commits ✅ |
| Broken Access Control | OWASP A01 | RBAC + harmonic permissions |
| Cryptographic Failures | OWASP A02 | FIPS 203/204/205 |

See: [`cybersecurity/attack-vectors/`](./cybersecurity/attack-vectors/)

---

## Compliance

| Framework | Coverage |
|---|---|
| ENISA NIS2 | Incident reporting, supply chain, encryption |
| NIST CSF 2.0 | Identify · Protect · Detect · Respond · Recover |
| NIST SP 800-207 | Zero Trust Architecture |
| ISO/IEC 27001:2022 | Information security controls |
| OWASP ASVS 4.0 | Application security verification |
| GDPR / LGPD | Data protection by design |

See: [`cybersecurity/compliance/`](./cybersecurity/compliance/)

---

## Parent Framework

👉 [Hubstry HALE Ecosystem](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
