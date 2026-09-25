# Project Kestrel

> [!WARNING]
> THIS IS ONLY FOR ROBIN THE MAKER OF THIS REPO, YOU WILL NOT GET ANY SUPPORT WHEN USING THESE IMAGES INSTEAD USE THIS AS A BASE FOR YOUR OWN.

One source of reason for Fedora Hummingbird images: **RPM factory** (Tine-built package factory) → **Warbler** (desktop) + **Woodpecker** (server).

## Architecture

```
Kestrel/
├── rpm-factory/       # Specs, verified source lock, Tine/Buck graph, OCI RPM repository
├── tine/               # Pinned Tine submodule
├── warbler/            # Desktop image — Mango + Quickshell + SDDM autologin
├── woodpecker/         # Server image — podman, cockpit, uupd, full hardware enablement
├── config/             # Shared config (flavors.json)
├── docs/               # Architecture, building, targeting-hummingbird
├── .github/workflows/  # CI/CD (build, test, sign, scan, promote)
└── .agents/skills/     # Agent skills for specialized tasks
```

## Images

| Image | Base | Description |
|-------|------|-------------|
| `ghcr.io/huntedraven7/rpm-factory` | — | Tine-built RPM repository consumed by Warbler/Woodpecker |
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

## Packages (RPM factory)

145 buildable recipes are tracked in `rpm-factory/config/upstream-sources.json`, with the complete
allow-list maintained separately from recipes that are not implemented yet.

All package builds:

- verify the SHA-512/signature pipeline before staging sources;
- build through the pinned `tine` submodule and its Fedora 46 buildroot;
- use the `.hum1.rpmfactory` RPM release suffix;
- emit binary and source RPMs through the Tine Buck graph;
- sign the published repository with cosign and attach SLSA provenance and an SBOM;
- scan the candidate image with Trivy (CRITICAL/HIGH blocks promotion).

## Planned: RPM factory builds every Atom

Long term, **every package installed in Warbler and Woodpecker will be built by RPM factory** — no Fedora or Hummingbird binaries at install time. Their repositories stay available as *buildroots only* (compilers, macros, bootstrap BuildRequires), never as install sources.

Today the images still consume some base packages directly; each one is tracked until it earns an RPM factory recipe:

- `upstream-sources.json` is the allow-list: a package with no entry cannot build or publish.
- `recalculate-gaps.yml` (every 6h) diffs the Hummingbird base + repository against the image contracts and reports what RPM factory still needs to absorb.
- Rule of thumb: leaf apps and the desktop stack first, toolchain and base libraries last — never rebuild what Hummingbird's hardened pipeline already owns unless the desktop needs a newer or different build.

## Security

- **Supply chain**: cosign keyless signing + SLSA provenance + SBOM (syft)
- **Vulnerability scanning**: Trivy on every publish (SARIF → GitHub Security)
- **Source verification**: `upstream-sources.json` allow-list, fail-closed
- **Tine pin**: the `tine` git submodule and the custom GitHub action verify the exact commit and Buck2 digest
- **No secrets**: All signing via OIDC, no keys in repo

## Development

### Prerequisites

- podman
- python3 + pytest
- just (command runner)
- Tine's Linux user namespaces and `zstd` (or Python 3.14+)

### Tine metadata

The specs and source lock are authoritative. The generated projection is checked in:

```sh
just tine-generate
just tine-check
just tine-build dconf
```

Use `just verify` as the complete local pre-commit gate (config checks, unit tests, and
Tine metadata). Use `just matrix` to inspect the exact chunk plan that CI will build, and
`just tine-build-chunk "pkg-one pkg-two"` to stage sources and build a group of packages the
same way the workflow does.

### Adding a Package

1. Add an entry to `rpm-factory/config/upstream-sources.json` with version and URL template.
2. Record its SHA-512 with `source_pipeline.py record <pkg>`.
3. Add the spec and sidecars under `rpm-factory/packages/<pkg>/`.
4. Regenerate the Tine projection with `just tine-generate`.
5. Update the `.packit.yaml` entry and the Warbler/Woodpecker contracts if needed.
6. Run `just verify` and build the affected package with `just tine-build <pkg>`.

### Importing from Fedora

```bash
# Via workflow (creates PR)
gh workflow run import-package.yml -f package=pkgname

# Or locally
./rpm-factory/tools/bulk-import.sh packages.txt
```

## References

**Docs**
- [AGENTS.md](AGENTS.md) — Agent instructions + skill router
- [docs/architecture.md](docs/architecture.md) — Architecture details
- [docs/building.md](docs/building.md) — Build instructions
- [docs/targeting-hummingbird.md](docs/targeting-hummingbird.md) — Hummingbird targeting
- [docs/SKILL.md](docs/SKILL.md) — Skill router

**Inspiration**
- [Utah](https://github.com/projectbluefin/utah) — Project Bluefins Fedora Hummingbird image!
- [Utah-Packages](https://github.com/projectbluefin/utah-packages) — The package factory for Utah!

## License

Apache-2.0
