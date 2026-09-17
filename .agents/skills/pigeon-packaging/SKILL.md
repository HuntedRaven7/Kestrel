---
name: pigeon-packaging
description: RPM recipes, specs, Mock/rpmbuild, Packit SRPMs
---
# Pigeon packaging

Recipes live in `pigeon/packages/<name>/` (spec + patches + `.hummingbird-upstream.json`).
Seed via `just import <pkg>` (dist-git rawhide → PR). Never hand-bump versions —
Packit + Renovate own updates (PLAN.md §3.2).
