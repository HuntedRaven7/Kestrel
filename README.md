# Project Kestrel

> One source of reason for Fedora Hummingbird images: **Pigeon** (package factory) → **Warbler** (desktop) + **Woodpecker** (server).

## Architecture

```
Kestrel/
├── pigeon/              # Package factory — builds RPMs, publishes OCI repo image
├── warbler/             # Desktop image — Mango + Quickshell + GDM autologin
├── woodpecker/          # Server image — podman, cockpit, uupd, full hardware enablement
├── config/              # Shared config (flavors.json)
├── docs/                # Architecture, building, targeting-hummingbird
├── .github/workflows/   # CI/CD (build, test, sign, scan, promote)
└── .agents/skills/      # Agent skills for specialized tasks
```

## Quick Start

```bash
# Validate configuration
just check

# Run tests
just test

# Build Pigeon package factory (local)
just build-pigeon

# Build Warbler desktop (flavor: main, nvidia, gaming, nvidia-gaming)
just build-warbler flavor=main

# Build Woodpecker server
just build-woodpecker

# Build ISO (requires bootc-image-builder)
just iso image=warbler flavor=main

# Import package from Fedora dist-git rawhide
just import pkg=wlroots

# Sync Bluefin base.toml for drift detection
just sync-bluefin-toml
```

## Images

| Image | Base | Description |
|-------|------|-------------|
| `ghcr.io/huntedraven7/pigeon` | — | RPM repository (consumed by Warbler/Woodpecker) |
| `ghcr.io/huntedraven7/warbler` | Hummingbird | Mango desktop (GDM + Quickshell) |
| `ghcr.io/huntedraven7/woodpecker` | Hummingbird | Server (podman, cockpit, uupd) |
| `ghcr.io/huntedraven7/warbler-kernel-cache` | Hummingbird | Prebuilt OGC kernel + NVIDIA modules |

### Flavors

| Flavor | Kernel | NVIDIA | Use Case |
|--------|--------|--------|----------|
| `main` | Base | No | Daily driver |
| `nvidia` | Base | Yes | NVIDIA GPU |
| `gaming` | OGC | No | Gaming (sched_ext, binderfs) |
| `nvidia-gaming` | OGC | Yes | Gaming + NVIDIA |

### Streams

- `:testing` — Development, boot-check gated
- `:stable` — Promoted from `:testing` after Trivy scan passes

## Packages (Pigeon)

52 packages in `pigeon/config/upstream-sources.json`, managed by Packit + Renovate.

**Priority packages (built in stages):**

| Stage | Packages |
|-------|----------|
| 0 | `wlroots 0.20.2`, `scenefx 0.5` |
| 1 | `mango 0.17.2`, `quickshell 0.3.1` |
| 2 | `awww 0.12.1`, `rofi 1.7.9.1`, `ghostty 1.3.1`, `kestrel-gdm-config` + portal stack |

All packages:
- Verified via `source_pipeline.py` (SHA-512 + optional signature verification)
- Built in `fedora:44` + Hummingbird COPR
- Signed with cosign keyless + SLSA attestation
- Scanned with Trivy (CRITICAL/HIGH blocks promotion)

## CI/CD

Workflows in `.github/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `validate.yml` | Factory contract, package config, unit tests |
| `rebuild-pigeon.yml` | Full Pigeon rebuild pipeline (stages 0-2 → precedence → publish) |
| `build-stage.yml` | Reusable RPM build stage (rpmbuild in fedora:44) |
| `build-warbler.yml` | Warbler image + ISO (per flavor, with kernel cache) |
| `build-woodpecker.yml` | Woodpecker server image |
| `build-iso.yml` | Standalone ISO build via bootc-image-builder |
| `import-package.yml` | Seed import from Fedora dist-git rawhide |
| `packit-srpm-pilot.yml` | SRPM generation verification |
| `recalculate-gaps.yml` | Scheduled (6h): diff installed vs contract |

## Security

- **Supply chain**: cosign keyless signing + SLSA provenance + SBOM (syft)
- **Vulnerability scanning**: Trivy on every publish (SARIF → GitHub Security)
- **Source verification**: `upstream-sources.json` allow-list, fail-closed
- **No secrets**: All signing via OIDC, no keys in repo

## Development

### Prerequisites

- podman
- python3 + pytest
- just (command runner)

### Adding a Package

1. Add entry to `pigeon/config/upstream-sources.json` with version + URL template
2. Run `source_pipeline.py record <pkg>` to fetch + record SHA-512
3. Add spec to `pigeon/packages/<pkg>/<pkg>.spec`
4. Add to `.packit.yaml` packages section
5. Update `warbler.toml` / `woodpecker.toml` contracts
6. Run `just check && just test`

### Importing from Fedora

```bash
# Via workflow (creates PR)
gh workflow run import-package.yml -f package=pkgname

# Or locally
./pigeon/tools/bulk-import.sh packages.txt
```

## References

- [PLAN.md](PLAN.md) — Full design document
- [AGENTS.md](AGENTS.md) — Agent instructions + skill router
- [docs/architecture.md](docs/architecture.md) — Architecture details
- [docs/building.md](docs/building.md) — Build instructions
- [docs/targeting-hummingbird.md](docs/targeting-hummingbird.md) — Hummingbird targeting
- [docs/SKILL.md](docs/SKILL.md) — Skill router

## License

Apache-2.0
