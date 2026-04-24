# Compliance & Regulatory Alignment

> **Coverage:** ENISA NIS2 · NIST CSF 2.0 · ISO 27001:2022 · OWASP ASVS · GDPR/LGPD

---

## ENISA NIS2 Directive (EU 2022/2555)

| Requirement | Implementation |
|---|---|
| Risk management | Attack vector matrix + HSL threat model |
| Incident handling | Response playbook (P1–P4 severity) |
| Supply chain security | SBOM + signed commits ✅ |
| Encryption | FIPS 203/204/205 + AES-256-GCM |
| Access control | RBAC mapped to harmonic hierarchy |
| MFA | HSL phase auth + TOTP/FIDO2 |
| 24h incident reporting | Automated alerting pipeline |

## NIST CSF 2.0

| Function | Implementation |
|---|---|
| GOVERN | Security policy in SECURITY.md |
| IDENTIFY | SBOM, asset inventory per harmonic zone |
| PROTECT | RBAC + HSL + MFA + PQC encryption |
| DETECT | Behavioral anomaly detection + SIEM |
| RESPOND | Incident response playbook |
| RECOVER | 3-2-1 backup + tested restore |

## NIST SP 800-207 — Zero Trust

| ZT Principle | HPG/HALE Implementation |
|---|---|
| Never trust, always verify | HSL challenge-response on every access |
| Verify explicitly | ML-DSA signed packets per channel |
| Least privilege | Harmonic address hierarchy = permission scope |
| Assume breach | Immutable audit logs + microsegmentation |

## ISO/IEC 27001:2022

| Control | Coverage |
|---|---|
| A.8.7 Malware protection | EDR + network segmentation |
| A.8.16 Monitoring | SIEM + anomaly detection |
| A.8.24 Cryptography | FIPS 203/204/205 + key management |
| A.8.28 Secure coding | OWASP ASVS Level 2 |

## OWASP ASVS 4.0 — Level 2 Target

| Chapter | Status |
|---|---|
| V2 Authentication | ✅ HSL + MFA + rate limiting |
| V3 Session | ✅ Nonce + timestamp binding |
| V6 Cryptography | ✅ FIPS 203/204/205 |
| V9 Communications | 🔄 TLS 1.3 + mTLS planned |
| V10 Malicious Code | ✅ CI/CD dependency scanning |

## GDPR / LGPD

| Principle | Implementation |
|---|---|
| Data minimization | IoT telemetry limits PII collection |
| Security | PQC encryption + RBAC |
| Privacy by design | Security embedded in HPG architecture |
| Breach notification | 72h workflow (LGPD Art. 48) |

See also: [`../../compliance/gdpr/`](../../compliance/gdpr/)

---

## Incident Response Playbook

```
P1 Critical (active breach)    → 1h response → isolate channel zone
P2 High (suspected compromise) → 4h response → capture logs
P3 Medium (policy violation)   → 24h response
P4 Low (informational)         → 72h response

P1 Procedure:
1. ISOLATE   → Disconnect affected harmonic zones
2. ASSESS    → Capture logs, identify blast radius
3. CONTAIN   → Revoke compromised ML-DSA certs / HSL tokens
4. NOTIFY    → ANPD (LGPD, 72h) / ENISA (NIS2, 24h if applicable)
5. ERADICATE → Patch + rotate all keys in affected zone
6. RECOVER   → Restore from last verified backup
7. LESSONS   → Post-incident report within 30 days
```

---

## Brazilian Editais Applicable

| Program | Relevance |
|---|---|
| FINEP CT-INFO | IoT + cybersecurity innovation |
| BNDES Mais Inovação | Deep tech, national security |
| MCTI — Hackers do Bem | Security education + tooling |
| ANPD regulatory compliance | LGPD technical implementation |
| GSI/PR | IoT security for critical gov systems |
| RNP — cybersecurity | Academic/research networks |
