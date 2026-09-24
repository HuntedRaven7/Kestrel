---
name: rpm-factory-source-verify
description: upstream-sources.json, source verification, Renovate bumps
---
# Source verification

`rpm-factory/config/upstream-sources.json` is the allow-list — no entry, no build. The existing
`source_pipeline.py` remains the SHA-512/signature boundary, and `stage_sources.py` adapts it to
Tine's per-package source inputs. Generated local archives are verified against the same lock before
staging. Generated Tine metadata is checked against the lock and specs with `just tine-check`; update
it with `just tine-generate` after a source or spec change.

awww is hand-vendored (Codeberg blocks scraping); record SHA-512 manually. Renovate owns source
versions; do not hand-edit versions in specs.
