# Project Kestrel

> [!WARNING]
> THIS IS ONLY FOR ROBIN THE MAKER OF THIS REPO, YOU WILL NOT GET ANY SUPPORT WHEN USING THESE IMAGES INSTEAD USE THIS AS A BASE FOR YOUR OWN.


One source of reason for Fedora Hummingbird images: **Pigeon** (package factory) → **Warbler** (desktop) + **Woodpecker** (server).

## Architecture

```
Swan/
├── pigeon/              # Package factory — builds RPMs, publishes OCI repo image
├── warbler/             # Desktop image — Mango + Quickshell + SDDM autologin
├── woodpecker/          # Server image — podman, cockpit, uupd, full hardware enablement
├── config/              # Shared config (flavors.json)
├── docs/                # Architecture, building, targeting-hummingbird
├── .github/workflows/   # CI/CD (build, test, sign, scan, promote)
└── .agents/skills/      # Agent skills for specialized tasks
```

## Images

| Image | Base | Description |
|-------|------|-------------|
| `ghcr.io/huntedraven7/pigeon` | — | RPM repository (consumed by Warbler/Woodpecker) |
| `ghcr.io/huntedraven7/warbler` | Hummingbird | Mango desktop (SDDM + Quickshell) |
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

145 packages in `pigeon/config/upstream-sources.json`, managed by Packit + Renovate.

All packages:
- Verified via `source_pipeline.py` (SHA-512 + optional signature verification)
- Built in a `fedora:44` container against the Hummingbird overlay repo
- Signed with cosign keyless + SLSA attestation
- Scanned with Trivy (CRITICAL/HIGH blocks promotion)

## Planned: Pigeon builds every Atom

Long term, **every package installed in Warbler and Woodpecker will be built by Pigeon** — no Fedora or Hummingbird binaries at install time. Their repositories stay available as *buildroots only* (compilers, macros, bootstrap BuildRequires), never as install sources.

Today the images still consume some base packages directly; each one is tracked until it earns a Pigeon recipe:

- `upstream-sources.json` is the allow-list: a package with no entry cannot build or publish.
- `recalculate-gaps.yml` (every 6h) diffs the Hummingbird base + repo against the image contracts and reports what Pigeon still needs to absorb.
- Rule of thumb: leaf apps and the desktop stack first, toolchain and base libraries last — never rebuild what Hummingbird's hardened pipeline already owns unless the desktop needs a newer or different build.

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

> Docs
- [AGENTS.md](AGENTS.md) — Agent instructions + skill router
- [docs/architecture.md](docs/architecture.md) — Architecture details
- [docs/building.md](docs/building.md) — Build instructions
- [docs/targeting-hummingbird.md](docs/targeting-hummingbird.md) — Hummingbird targeting
- [docs/SKILL.md](docs/SKILL.md) — Skill router

> Inspiration
- [Utah](https://github.com/projectbluefin/utah)
- [Utah-Packages](https://github.com/projectbluefin/utah-packages)

## License

Apache-2.0
