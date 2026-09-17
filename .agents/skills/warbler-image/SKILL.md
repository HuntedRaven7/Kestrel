---
name: warbler-image
description: Warbler Containerfile, contracts, system_files, ISO
---
# Warbler image

`warbler/Containerfile` consumes `ghcr.io/huntedraven7/pigeon` by digest.
Contracts in `warbler/packages/*.toml`; verify scripts assert the installed set.
Flavors from `config/flavors.json`. ISO via `just iso warbler` (phase-6).
