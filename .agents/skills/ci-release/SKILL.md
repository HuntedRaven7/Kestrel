---
name: ci-release
description: GitHub Actions, projectbluefin/actions, signing, promotion
---
# CI / release

Pin `projectbluefin/actions/bootc-build/*@v1`; third-party actions by full SHA.
Streams `:testing` → `:stable` per `config/flavors.json`.
cosign keyless + SLSA attestation + Trivy scan on every publish.
