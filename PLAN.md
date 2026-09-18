# Kestrel — PLAN.md

> Monorepo for Fedora Hummingbird images: **Pigeon** (package factory) →
> **Warbler** (desktop) + **Woodpecker** (server).
> Owner: `huntedraven7` (lowercase, GHCR requirement).
> Base: `quay.io/hummingbird-community/bootc-os`, digest-pinned, x86_64 for v1.

## 0. Decisions (locked)

| # | Decision |
|---|---|
| 1 | Single repo `HuntedRaven7/Kestrel` with Bluefin-style digest seam: `pigeon/` publishes `ghcr.io/huntedraven7/pigeon` OCI repo image; `warbler/` + `woodpecker/` consume via `COPY --from=` pinned by digest. Every branch publishes under its own tag. |
| 2 | GHCR owner is `huntedraven7` (lowercase). RPM release suffix is `.hum1.pigeon` (e.g. `mango-0.17.2-1.hum1.pigeon`). Never reuse `.hum1.bfin`. |
| 3 | Pigeon scope: **full desktop-stack fork** in the style of `projectbluefin/utah-packages` (~190 RPMs over time), but land the 6 priority packages first to reach first boot, then expand. |
| 4 | Warbler session: **SDDM + Mango session** with SDDM autologin drop-in (`sddm.conf.d`, maldives theme, no breeze dep). Mango autostarts Quickshell; **no default Quickshell config shipped** — user owns `~/.config/quickshell`. |
| 5 | Quickshell: **build whatever Quickshell v0.3.1 needs** (Qt + private headers, full feature set). Couple Quickshell rebuilds to Qt updates via Renovate + Packit. |
| 6 | Launcher/terminal: stock **`rofi`** + **`ghostty`** (build ghostty in Pigeon). |
| 7 | Flavors: v1 includes **NVIDIA + OGC kernel** path (like Utah `nvidia`/`gaming` flavors). OGC kernel builds/asserts before NVIDIA module. |
| 8 | awww v0.12.1: license GPL-3.0, source vendored manually from Codeberg tarball. Mango default config: **plain upstream** (`DreamMaoMao/mango-config` daily default or `/etc/mango/config.conf` as-shipped). |
| 9 | Updates: **Packit + Renovate** own all version bumps (upstream-sources + specs + digests + GHCR/base pins). This is a mental-health requirement: no hand-bumped versions. |
| 10 | Docs/skills: Dakota-style `AGENTS.md` + `docs/SKILL.md` router + `.agents/skills/*` + `docs/skills/*`. |

## 1. References

* Factory model: `projectbluefin/utah-packages` (builds GNOME 51 + stack, publishes OCI repo, `COPY --from=` digest seam).
* Image model: `projectbluefin/utah` (`Containerfile` layer discipline, `packages/*.toml` contracts, `verify-*.py`, `configure-services.sh`, `Containerfile.kernel`, OGC + NVIDIA flow).
* CI primitives: `projectbluefin/actions` `bootc-build/*@v1` + reusable `reusable-build.yml` / `reusable-release.yml`.
* Agent model: `projectbluefin/dakota` (`AGENTS.md`, `.agents/skills/*`, skill router, `just validate`).
* Hummingbird base: `quay.io/hummingbird-community/bootc-os` (rolling, image-based, ~95% Rawhide-derived). Hummingbird supplies hardened bootable base + no desktop.

## 2. Repo layout (target)

```text
Kestrel/
  PLAN.md
  AGENTS.md
  Justfile
  renovate.json
  .packit.yaml
  .github/workflows/
    validate.yml
    rebuild-pigeon.yml
    build-stage.yml          # 1 per wave, stages 0-4
    build-warbler.yml
    build-woodpecker.yml
    import-package.yml
    packit-srpm-pilot.yml
    recalculate-gaps.yml
  pigeon/
    packages/<name>/         # <name>.spec + patches + .hummingbird-upstream.json
    config/upstream-sources.json
    config/factory-contract.json
    tools/{source_pipeline.py,packit_workflow.py,validate.py,publish_gate.py,factory_contract.py}
    tests/
  warbler/
    Containerfile
    Containerfile.kernel
    packages/{bluefin.toml,warbler.toml}
    contracts/desktop.toml
    system_files/shared/     # sddm autologin, mango.desktop, mango defaults, rofi theme, ghostty preset, awww user unit
    scripts/{install-packages.py,verify-rpm-contract.py,configure-services.sh,configure-branding.sh,clean-stage.sh,install-ogc-kernel.sh,install-nvidia.sh}
    iso/
  woodpecker/
    Containerfile
    packages/woodpecker.toml
    system_files/shared/
    scripts/
  docs/{architecture.md,building.md,targeting-hummingbird.md,verification/,skills/}
  .agents/skills/{pigeon-packaging,pigeon-source-verify,warbler-image,woodpecker-server,mango-quickshell,sddm-autologin,ci-release,review}/
```

## 3. Pigeon — package factory

### 3.1 Contract

* Output: `ghcr.io/huntedraven7/pigeon` — image whose only content is `createrepo_c` output under `/repository`, cosign-signed + SLSA-attested. `main` → `:latest`; every other branch → `:<branch>`.
* Consumers pin it: `ARG PIGEON_IMAGE=ghcr.io/huntedraven7/pigeon` + `ARG PIGEON_IMAGE_SHA=sha256:…`, `COPY --from=pigeon /repository /etc/pigeon`. Renovate updates the SHA.
* RPM suffix `.hum1.pigeon`. `precedence` job enforces each RPM outranks Fedora 44 + Hummingbird and reports undeclared overlap.

### 3.2 Source model (Packit + Renovate owned)

* Fedora dist-git `rawhide` import = **seed only**. `import-package.yml` imports into `pigeon/packages/<name>/`, writes `.hummingbird-upstream.json` (remote, commit, tree, time), opens a PR. Downstream patches stay explicit.
* `pigeon/config/upstream-sources.json` = allow-list. No entry → no build. Entry shape:

```json
{
  "packages": {
    "mango": {
      "version": "0.17.2",
      "url_template": "https://github.com/mangowm/mango/archive/refs/tags/{version}.tar.gz",
      "sha512": "<recorded>",
      "renovate": { "datasource": "github-tags", "depName": "mangowm/mango" }
    }
  }
}
```

* `tools/source_pipeline.py` fetches direct upstream archive/tag, verifies SHA-512 (+ sig/GPG when upstream offers it), writes report, fails closed.
* **Packit**: root `.packit.yaml` covers every recipe (SRPM via `packit srpm --preserve-spec` in `packit-srpm-pilot.yml`, then binary lane). Packit jobs propose/handle spec + source bumps; merge only after verified RPM build gate + recorded new digest/signature.
* **Renovate**: `renovate.json` watches `upstream-sources.json` (`github-tags`, `crate`, `pypi`, custom regex for Codeberg), `Containerfile` ARGs (`UUPD_VERSION`+SHA, base digests, `PIGEON_IMAGE_SHA`), and `projectbluefin/actions@v1`. `upstream-source` PRs automerge only after build gate passes.

### 3.3 Priority packages (phase 1, in build order)

| Stage | Package | Version / source | Notes |
|---|---|---|---|
| 0 | `wlroots` | **0.19.2**, freedesktop gitlab | Mango hard-requires 0.19.x. If Hummingbird ships 0.20.x, vendor 0.19.2 in Pigeon (parallel or renamed). Check first. |
| 0 | `scenefx` | **≥0.4.1** (0.4.1 known-good), `github.com/wlrfx/scenefx` | Mango effects backend. |
| 1 | `mango` | **0.17.2**, `github.com/mangowm/mango` | meson+ninja. Deps: `wayland≥1.23.1, wayland-protocols, libinput≥1.27.1, libxkbcommon, pcre2, pixman, libdrm, libdisplay-info, libliftoff, hwdata, seatd, xorg-xwayland, libxcb, xcb-icccm, cjson, pango`. Ship `/etc/mango/config.conf` (upstream default). |
| 1 | `quickshell` | **v0.3.1**, `quickshell-mirror/quickshell` (tag `1a4716c`, GPG-signed) | cmake+ninja. Build **full feature set**: `qt6-base, qt6-declarative (+private), qt6-wayland (+private if Qt<6.10), qt6-svg, qt6-shadertools, spirv-tools, wayland, wayland-protocols, cli11, cpptrace, pipewire, pam, polkit, jemalloc, libdrm, libEGL/GLES`. At least Qt 6.6. Rebuild on every Qt release (private-API ABI). |
| 2 | `awww` | **v0.12.1**, `https://codeberg.org/LGFae/awww/archive/v0.12.1.tar.gz`, GPL-3.0 | Codeberg blocks scraping → human vendors tarball once, records SHA-512; pipeline verifies locally thereafter. Confirm Rust vs C on download; if Rust, add offline cargo vendor step. Ship `awww.service --user`. |
| 2 | `rofi` | stock `rofi` (X11) per request | Note: stock rofi is X11-only; works via XWayland under Mango. If native Wayland launcher needed later, evaluate `rofi-wayland` fork as separate package. |
| 2 | `ghostty` | latest stable, `github.com/ghostty-org/ghostty` | Likely Zig; needs Zig toolchain in buildroot + shell/completion assets. Renovate `github-tags`. |
| 2 | `sddm` | **0.21.0**, `github.com/sddm/sddm` | Fedora dist-git import. Display manager; autologin into Mango via `sddm.conf.d` drop-in, maldives theme (no breeze/plasma dep). No custom config package (dropped `kestrel-gdm-config`). |
| 2 | support set | from Fedora/Hummingbird where present, else Pigeon | `xdg-desktop-portal-wlr, seatd, wl-clipboard, grim, slurp, swayidle, swaylock, brightnessctl, pamixer, xfce-polkit, foot (fallback)` |

### 3.4 Build pipeline

* Runners: GitHub-hosted `ubuntu-24.04` now, track `ubuntu-26.04` migration. Build container `quay.io/fedora/fedora:44` (+ Hummingbird repos) for BuildRequires; record decision to move to Mock-hermetic + `buildroot_lock.json` as follow-up (do not claim Mock until real).
* `rebuild-pigeon.yml`: `prepare` (new/changed/full-rebuild → stage lists 0-4) → `preflight` (advisory BuildRequires resolve, `continue-on-error`) → `rebuild0..4` (`build-stage.yml` matrices, `fail-fast:false`, prior artifacts as local `[stages]` repo, `rpmbuild -br` then `-ba`) → `precedence` → `publish` (merge, drop bootstrap RPM, `createrepo_c`, sign `repomd.xml` keyless cosign/OIDC, Hummingbird-only transaction check via `publish_gate.py`, push OCI + attest).
* `recalculate-gaps.yml` (6h): pull Hummingbird bootc image, union installed RPMs + live repo, diff vs Warbler/Woodpecker contracts, publish artifact.
* `validate.yml` on PR/push: `factory_contract.py` (skill index, front-matter, AGENTS mandate, no changelog/session-notes, links resolve) + `validate.py` (provenance + source-lock + Packit coverage for every recipe) + `pytest tests/` + pre-commit (yaml/json/toml, actionlint, third-party SHA pins).

## 4. Warbler — desktop image

* `warbler/Containerfile` (follow Utah layer discipline: few COPYs, fold small RUNs, declare `VERSION`/flavor ARGs late):
  `BASE_IMAGE` (pinned Hummingbird digest) + `PIGEON_IMAGE_REF` (pinned digest) + `common`/`brew` sidecars (optional; decide: include `projectbluefin/common` + `ublue-os/brew` like Utah, or go without for v1 — recommend **without** for first boot, add when branding/flatpaks needed) → copy manifests + repo files + `/etc/pigeon` → `install-packages.py` → `verify-rpm-contract.py` → Quickshell/Mango/awww/rofi/ghostty config → `configure-services.sh` (desktop service policy, SDDM enable, login defaults, update policy) → `configure-branding.sh` → `verify-desktop-contract.py` → OGC/NVIDIA per flavor → `clean-stage.sh` + `bootc container lint --fatal-warnings`.
* Contracts: `packages/bluefin.toml` byte-copy of Bluefin `base.toml` (CI diffs, drift fails build) + `packages/warbler.toml` (Mango, quickshell, awww, rofi, ghostty, `sddm`, portal stack, `[unavailable]` with issue links). Resolved list written to `/usr/share/warbler/contract.txt`; verify asserts that file.
* SDDM autologin (`system_files/shared/etc/sddm.conf.d/10-warbler-autologin.conf`):
  `[Autologin] User=<user>, Session=mango.desktop` + `[Theme] Current=maldives`. User created at install; document as opt-in kiosk default, never a baked known password.
* Mango session (`share/wayland-sessions/mango.desktop`): `Exec=/usr/bin/mango`, `DesktopNames=mango`. Mango config = upstream default; user overrides in `~/.config/mango`.
* Quickshell: autostart `quickshell.service --user` from Mango config; **ship no `shell.qml`** (user-owned). Ensure `qs -c` / `qs -p` work + QML debugger path documented.
* Flavors (`config/flavors.json` single source): `warbler` (main), `warbler-nvidia`, `warbler-gaming`, `warbler-nvidia-gaming`. `Containerfile.kernel` builds OGC kernel (`sched_ext`, `binderfs`); `install-nvidia.sh` binds module to exact kernel tree. OGC asserts before NVIDIA.
* ISO: `bootc-image-builder` live ISO (`just iso`); installer payload = next milestone after SDDM→Mango verified.

## 5. Woodpecker — server image

* Bluefin-server-like: Hummingbird base + `cockpit, podman, skopeo, uupd (pinned version+SHA, Renovate-owned), bootc-auto-update timer, tailscale/wireguard-tools, openssh-server (ENABLE_SSHD=0 default)`, dev/container tooling. No SDDM/Mango/Quickshell/rofi/awww/ghostty.
* Shares Warbler base stages where possible (same `Containerfile` preamble pattern), stops before GUI layer. Same signing/SBOM/Trivy/QEMU-boot gates.

## 6. CI (projectbluefin/actions)

* Pin `projectbluefin/actions/bootc-build/*@v1`; third-party actions by full SHA + version comment.
* Use: `setup-runner, dnf-cache, preflight, detect-changes, validate-pr, generate-tags, push-image, create-manifest (multi-arch later), sign-and-publish (cosign+SBOM+SLSA), scan-image (Trivy→SARIF, auto-file CVE issues on main), rechunk/chunka, generate-release-notes (git-cliff)`.
* Image streams: `:testing` (dev, boot-check gated) → promoted `:stable`. Flavors × streams from `config/flavors.json`.

## 7. Docs + agent skills (Dakota-style)

* `AGENTS.md` = authority for agents; skill router table (`pigeon-packaging, pigeon-source-verify, warbler-image, woodpecker-server, mango-quickshell, sddm-autologin, ci-release, review`). Load only matching skill.
* `just check` (factory contract + package config) / `just test` (pytest). No committed changelogs or session notes; skills are evergreen invariants, not dated logs.
* Human docs: `docs/building.md, docs/architecture.md, docs/targeting-hummingbird.md, docs/verification/`.

## 8. Execution phases

1. **Scaffold**: dirs above + `AGENTS.md`, `Justfile`, `renovate.json`, `.packit.yaml`, `validate.yml`, `factory_contract.py`, `SKILL.md` stubs.
2. **Pigeon bootstrap**: `upstream-sources.json` (wlroots, scenefx, mango, quickshell, awww, rofi, ghostty) + `source_pipeline.py` + `build-stage.yml` + publish `:latest`.
3. **Packit+Renovate wiring**: `.packit.yaml` all-recipes coverage, Renovate rules (upstream tags, Codeberg custom, digest pins, Qt→quickshell coupling). Verify a bump PR end-to-end.
4. **Warbler boot**: `Containerfile` + contracts + SDDM/Mango, QEMU to SDDM, `bootc lint` clean. No NVIDIA yet.
5. **Shell integration**: Mango autostart of user Quickshell, rofi keybind, awww user unit, ghostty default, autologin verify.
6. **NVIDIA/OGC + Woodpecker + ISO**: `Containerfile.kernel`, flavor matrix, server image, live ISO.
7. **Hardening**: cosign/SLSA/SBOM/Trivy, `recalculate-gaps`, promotion `:testing→:stable`, verification screenshots (`docs/verification/`).
8. **Full-fork expansion**: remaining ~190 imports to parity with Bluefin contract.

## 9. Risks

* wlroots 0.19.2 vs Hummingbird's version — first thing to check; parallel-vendor if mismatched.
* Quickshell Qt private-API ABI — every Qt bump needs quickshell rebuild; Renovate coupling is load-bearing.
* Full-fork maintenance (~190 pkgs on 4vCPU/6h runners) — phase 8 is long; phases 2-5 deliver value first.
* awww Codeberg anti-AI scraping — manual vendor step, keep tarball+SHA in-repo.
* SDDM autologin security — opt-in, documented, no default passwords.
* NVIDIA-on-OGC + gaming flavors unproven (same caveat as Utah) — isolate in flavor matrix so `main` stays green.

## 10. `just` starting set

```text
just check    # factory contract + package config
just test     # pytest
just build-pigeon
just build-warbler [flavor]
just build-woodpecker
just iso [warbler|woodpecker]
just qemu-boot [image]
just import <pkg>   # dist-git seed → PR
just bump-check     # renovate + packit status
```
