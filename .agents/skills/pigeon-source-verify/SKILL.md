---
name: pigeon-source-verify
description: upstream-sources.json, source verification, Renovate bumps
---
# Source verification

`pigeon/config/upstream-sources.json` is the allow-list — no entry, no build.
`source_pipeline.py` fails closed on missing digest/signature.
awww is hand-vendored (Codeberg blocks scraping); record SHA-512 manually.
