# Changelog

## 0.1.2

- Add app-local ISRG Root X1 and USERTrust ECC public roots to address older head-unit certificate stores.
- Retain system trust, hostname and certificate validation, TLS 1.2+, approved hosts, and ZIP integrity checks.
- Add TLS tests for supplemental trust, existing trust, unknown issuers, expired certificates, and wrong hostnames; verify GitHub downloads against a simulated stale system trust store.
- No system certificate-store or vehicle-setting changes.


## 0.1.1 — 2026-10-28

- Rename the on-car browser to RepoMan and move it to `apbreck/RepoMan`.
- Fetch the catalog from the new repository and publish RepoMan installers and the Hello test package there.
- Keep the original Android package, NEMESIS ID, and signing key for upgrades.
- Keep Camera Inventory in its existing repository, explicitly allowing downloads from these two owned projects.
- Retain the prototype’s experimental status and parked-state/verification checks.
