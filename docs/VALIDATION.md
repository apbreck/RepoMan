# Validation

The original browser prototype completed these checks on October 28, 2026:

- Java 8 compilation and Android API 19 DEX/APK generation.
- APK signature verification constrained to API 19.
- Unit tests for repository/HTTPS restrictions, transport destinations, hash and size mismatch, package identity, traversal, USB wrappers, and duplicate metadata.
- Android API 35 emulator loaded a loopback test catalog and verified a module ZIP.
- A corrupt download was rejected before any privileged command.
- Canceling confirmation invoked no installer.
- A failing fixture parked-state check blocked installation.
- Explicit confirmation invoked the fixture installer and the installed descriptor version was checked.
- The fixture installed-package list was refreshed.

[Compact emulator results](emulator-results.json). The fixture does not execute NEMESIS or vehicle-changing code.

Not validated: Android 4.4 TLS certificates/networking, actual NEMESIS command permissions/private-file access, actual Hyundai parked-state getters, physical-head-unit install/update behavior, or other Gen5W models. The Hello package is the intended first parked hardware test.

## Original prototype GitHub endpoint check

After publication, the same browser build fetched the public HTTPS catalog from GitHub, followed GitHub’s release-asset redirect, and verified the published Hello ZIP against the catalog. No install was attempted during this network check. This confirms the real GitHub path in the emulator, not Android 4.4 certificate compatibility.

## RepoMan 0.1.1

- Rebuilt with Java 8/API 19 and passed package/repository validation tests, including both approved repositories and rejection of an unapproved repository.
- Verified APK signatures for API 19.
- Installed the original browser APK, then updated it to RepoMan 0.1.1 with Android’s update installer in an API 35 emulator; the update succeeded with the retained package and signing identity.
- Vehicle installation remains unverified.

The published RepoMan HTTPS catalog loaded successfully in the emulator. The Hello ZIP downloaded from the new repository’s v0.1.1 release and passed size, hash, and package checks. No installation was attempted in this network check. [Screenshot](github-catalog.png).
