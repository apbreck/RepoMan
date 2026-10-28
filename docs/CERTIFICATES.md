# RepoMan certificate compatibility

The physical head unit reported `SSLHandshakeException` / `CertPathValidatorException: Trust anchor for certification path not found` with 0.1.1. This establishes a certificate-chain trust failure; it does not by itself identify the missing root on that unit.

On October 28, 2026, authenticated OpenSSL checks of all four approved GitHub hosts showed:

- raw.githubusercontent.com, release-assets.githubusercontent.com, objects.githubusercontent.com: Let’s Encrypt YR1 → Root YR cross-sign → ISRG Root X1.
- github.com: Sectigo DV E36 → Sectigo Root E46 cross-sign → USERTrust ECC Certification Authority.

## Public roots included in the APK

| Certificate | SHA-256 fingerprint of DER certificate | Source |
| --- | --- | --- |
| ISRG Root X1 | `96bcec06264976f37460779acf28c5a7cfe8a3c0aae11a8ffcee05c0bddf08c6` | [Issuer PEM](https://letsencrypt.org/certs/isrgrootx1.pem) |
| USERTrust ECC Certification Authority | `4ff460d54b9c86dabfbcfc5712e0400d2bed3fbc4d4fbdaa86e06adcd2a9ad7a` | [Sectigo root list](https://www.sectigo.com/knowledge-base/detail/Sectigo-Root-Certificates), [Microsoft CCADB report](https://ccadb.my.salesforce-sites.com/microsoft/IncludedCACertificateReportForMSFT) |

ISRG was fetched over verified HTTPS and matched the locally installed Mozilla-derived CA bundle. USERTrust ECC was extracted from that bundle after the issuer download endpoint refused a TLS handshake; its fingerprint matches the independent CCADB report. Only these two public, self-signed root certificates are packaged. No private keys, peer leaf certificates, or runtime-downloaded trust material are included.

The platform X509TrustManager validates the chain first. If it reports a certificate validation failure, a second standard X509TrustManager validates it against these app-bundled roots. Both paths require a valid leaf lifetime. HttpsURLConnection retains its default hostname verification; there is no global SSL override. The URL/redirect allowlist still restricts requests to approved GitHub hosts. A missing or invalid bundled certificate fails closed. The system trust store is never modified.

The supplemental roots are shipped inside the signed APK. Future CA changes may need another app update. This is not leaf/public-key pinning: valid certificate renewals under the trusted roots continue to work.

## Verification

`python3 tests/test_tls.py --live` creates temporary local CA/server fixtures and runs the production trust code:

- A certificate missing from the simulated system store succeeds with its supplemental CA.
- Existing system CA trust is retained.
- Unknown issuers, expired leaves, wrong hostnames, and empty root inputs fail.
- Live GitHub catalog retrieval and release redirect/download/package verification succeed with an unrelated CA as the JVM’s entire simulated system trust store, so the supplemental public roots are required.

This does not emulate Android 4.4’s TLS implementation. Physical-head-unit verification is still needed. No certificate checks are bypassed for that limitation. [Android’s guidance](https://developer.android.com/privacy-and-security/security-ssl) describes the error and the requirement to validate the issuer rather than use a permissive TrustManager.
