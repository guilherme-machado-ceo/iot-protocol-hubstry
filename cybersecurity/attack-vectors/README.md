# Attack Vectors & Mitigations

> **Sources:** ENISA Threat Landscape 2025 · OWASP Top 10 2025 · NIST CSF 2.0
> **Coverage:** 14 attack vectors with HPG/HALE-native mitigations

---

## Threat Matrix

| # | Vector | ENISA 2025 | OWASP 2025 | Severity | Mitigation |
|---|---|---|---|---|---|
| 1 | DDoS | 77% incidents | — | Critical | Channel isolation, rate limiting |
| 2 | Phishing | 60% intrusions | A07 | High | HSL auth, MFA, ML-DSA |
| 3 | Ransomware | #1 by damage | — | Critical | Immutable logs, segmentation |
| 4 | SQL Injection | — | A05 | High | Parameterized queries, ORM |
| 5 | Brute Force | — | A07 | High | Backoff, HSL tokens |
| 6 | Supply Chain | Most impactful | A06 | Critical | SBOM, signed commits ✅ |
| 7 | MitM | — | A02 | High | ML-KEM, mTLS, HSL |
| 8 | Replay Attack | — | A07 | Medium | Nonces, timestamp binding |
| 9 | Broken Access Control | — | A01 | Critical | RBAC + harmonic permissions |
| 10 | Cryptographic Failures | — | A02 | Critical | FIPS 203/204/205 |
| 11 | AI-Enhanced Attacks | Emerging | — | High | Behavioral anomaly detection |
| 12 | Side-Channel | — | — | Medium | Constant-time PQC ops |
| 13 | Misconfiguration | — | A05 | High | IaC hardening, CIS benchmarks |
| 14 | Zero-Day | — | A08 | Critical | SBOM + runtime monitoring |

---

## 1. DDoS
**ENISA 2025:** 77% of all incidents — dominant attack type in EU.

HPG-native mitigation: harmonic channel structure provides **natural traffic isolation** — flood on one channel (a/b·f₀) cannot saturate others due to spectral separation.

Checklist:
- [ ] Rate limiting per harmonic channel (token bucket)
- [ ] SYN cookies for TCP flood protection
- [ ] Anycast routing + scrubbing center integration
- [ ] IoT device registration limits (prevent botnet enrollment)

---

## 2. Phishing / Social Engineering
**ENISA 2025:** 60% of successful intrusions begin with phishing. AI-generated lures emerging.

HSL mitigation: phase-based device authentication means phished credentials alone cannot impersonate a device without correct harmonic phase response.

Checklist:
- [ ] HSL challenge-response for device auth
- [ ] FIDO2/passkeys for human accounts
- [ ] ML-DSA signed communications
- [ ] DMARC/DKIM/SPF on all email domains
- [ ] Anti-phishing simulation (quarterly)

---

## 3. Ransomware
**ENISA 2025:** #1 by damage. Average ransom demand +40% YoY despite 11% volume decrease.

Checklist:
- [ ] Immutable air-gapped backups (3-2-1 rule)
- [ ] Network segmentation via harmonic channel zones
- [ ] EDR on all endpoints
- [ ] Patch CVSS ≥ 7.0 within 72 hours
- [ ] Tested incident response playbook (quarterly drill)

---

## 4. SQL Injection & Code Injection
**OWASP 2025:** A05 — includes SQL, NoSQL, LDAP, OS command injection.

```python
# WRONG — vulnerable
query = f"SELECT * FROM devices WHERE id = '{device_id}'"

# CORRECT — parameterized
cursor.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
```

Checklist:
- [ ] Parameterized queries — always, no exceptions
- [ ] ORM with built-in sanitization
- [ ] WAF rules for injection patterns
- [ ] Regular DAST scans (OWASP ZAP / Burp Suite)

---

## 5. Brute Force & Credential Stuffing
**OWASP 2025:** A07 — authentication failures.

HSL mitigation: phase tokens are time-bound and channel-specific — captured token invalid after phase cycle.

Checklist:
- [ ] Max 5 attempts / 15 min per IP+device
- [ ] Exponential backoff with jitter
- [ ] HSL harmonic tokens (no static device passwords)
- [ ] MFA (TOTP/FIDO2) for human accounts
- [ ] Argon2id for password hashing

---

## 6. Supply Chain Attacks
**ENISA 2025:** Most impactful category — cascading consequences across sectors.

Checklist:
- [ ] SBOM on every build
- [ ] Signed commits on `master` ✅ (already configured)
- [ ] Dependency pinning with hash verification
- [ ] SLSA level 2+ target
- [ ] Dependabot / Snyk automated scanning
- [ ] Container image signing (Sigstore/Cosign)

---

## 7. Man-in-the-Middle (MitM)
Critical for IoT on untrusted networks (LoRaWAN, Zigbee, BLE).

ML-KEM-768 provides **post-quantum forward secrecy** — past sessions safe even if future quantum computer compromises key material.

Checklist:
- [ ] TLS 1.3 minimum (no TLS 1.0/1.1/SSL)
- [ ] Certificate pinning for IoT devices
- [ ] ML-KEM hybrid session key exchange
- [ ] mTLS for device-to-gateway communication

---

## 8. Replay Attacks
HPG mitigation: harmonic phase is time-dependent — valid response expires with phase cycle.

Checklist:
- [ ] Cryptographic nonces in all auth flows
- [ ] Timestamp binding ±30 second tolerance
- [ ] Sequence numbers on channels
- [ ] ML-DSA signed nonces

---

## 9. Broken Access Control
**OWASP 2025:** A01 — #1 most critical risk.

HALE mitigation: harmonic address hierarchy maps naturally to role hierarchy — device at (a/b) accesses only equal or lower-denominator resources by mathematical default.

Checklist:
- [ ] RBAC mapped to harmonic channel zones
- [ ] Deny by default
- [ ] Short-lived JWTs + refresh token rotation
- [ ] Quarterly access reviews

---

## 10. Cryptographic Failures
**OWASP 2025:** A02. No hardcoded keys, no MD5/SHA1/DES.

Checklist:
- [ ] AES-256-GCM for symmetric encryption
- [ ] ML-KEM-768 for key exchange (FIPS 203)
- [ ] ML-DSA-65 for signatures (FIPS 204)
- [ ] 90-day key rotation policy
- [ ] Secrets scanning in CI/CD (GitLeaks, TruffleHog)

---

## 11. AI-Enhanced Attacks (Emerging)
**ENISA 2025:** State-aligned and criminal actors using AI for targeting, evasion, and phishing personalization.

Checklist:
- [ ] Behavioral anomaly detection (ML baseline deviation)
- [ ] AI-generated content detection for email
- [ ] Red team exercises including AI-assisted attack simulation
- [ ] Honeypots / deception technology

---

## 12–14. Side-Channel, Misconfiguration, Zero-Day

- **Side-channel:** Constant-time PQC ops (liboqs provides this)
- **Misconfiguration:** IaC linting (Checkov/tfsec), CIS benchmarks
- **Zero-day:** CVE monitoring, vulnerability disclosure program (SECURITY.md)

---

## References
- [ENISA Threat Landscape 2025](https://www.enisa.europa.eu/publications/enisa-threat-landscape-2025)
- [OWASP Top 10 2025](https://owasp.org/Top10/2025/)
- [NIST CSF 2.0](https://www.nist.gov/cyberframework)
- [HALE Framework](https://github.com/guilherme-machado-ceo/hubstry-hale-ecosystem)
