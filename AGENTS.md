# Kestrel agent guide

Kestrel is a monorepo for Fedora Hummingbird bootc images. `pigeon/`
builds RPMs and publishes `ghcr.io/huntedraven7/pigeon` (OCI repo image).
`warbler/` (desktop: Mango + Quickshell + SDDM autologin) and `woodpecker/`
(server) consume it via `COPY --from=` pinned by digest. See `PLAN.md`.

Skills live in `.agents/skills/` and are discovered by Pi and GitHub Copilot.
Load only the skill matching the task; do not read every skill.

## Skill routing

| Task / Domain | Skill to load |
|---|---|
| RPM recipes, specs, Mock/rpmbuild, SRPM builds | `pigeon-packaging` |
| `upstream-sources.json`, source verification, Renovate bumps | `pigeon-source-verify` |
| Warbler Containerfile, contracts, system_files, ISO | `warbler-image` |
| Woodpecker server image, services, uupd | `woodpecker-server` |
| Mango compositor, Quickshell, rofi, ghostty, awww integration | `mango-quickshell` |
| SDDM autologin, session files, login policy | `sddm-autologin` |
| GitHub Actions, `projectbluefin/actions`, signing, promotion | `ci-release` |
| Reviewing PRs, triage, issue labels | `review` |

## Non-negotiable safety

- Never push directly to `main`. Work on a feature branch; human merges.
- Never expose secrets or weaken signing, provenance, or supply-chain checks.
- Do not post GitHub comments/reviews unless explicitly asked.
- SDDM autologin is opt-in kiosk behavior: never bake in a known password.
- A package with no `upstream-sources.json` entry must not build or publish.

## Sources of truth

1. Read the file being changed and its callers before editing.
2. `PLAN.md` for locked decisions (GHCR owner, `.hum1.pigeon` suffix, Renovate-owned lock versions).
3. Workflows, `Justfile`, and `tools/` output are current truth; prose that disagrees is stale.
4. Verify external syntax against current official docs before changing Containerfile, Renovate, cosign, or bootc usage.

## Development workflow

- `just --list` before inventing maintenance commands.
- `just check` for config changes; `just test` for `tools/` changes.
- Commits use `<type>(<scope>): <description>`.
- Version bumps come from Renovate PRs (lock) carried into specs via `just sync-versions`, never hand-edited versions.
