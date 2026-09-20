---
name: pigeon-packaging
description: RPM recipes, specs, Mock/rpmbuild, SRPM builds
---
# Pigeon packaging

Recipes live in `pigeon/packages/<name>/` (spec + patches + `.hummingbird-upstream.json`).
Seed via `just import <pkg>` (dist-git rawhide → PR). Never hand-bump versions —
Renovate owns lock bumps and `just sync-versions` carries them into specs (PLAN.md §3.2).

Build an SRPM locally with `just srpm <pkg>` (fetch + verify + audit-fix +
`rpmbuild -bs`); CI produces one per package on every build via `rpmbuild -br`
into the stage artifacts. No Packit lane exists.
