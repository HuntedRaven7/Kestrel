"""Validate factory config: provenance + source-lock + version sync.

Fails if any recipe dir lacks a source entry, if any source entry's
filename no longer matches its rendered URL basename, or if any spec
Version: disagrees with the lock (the lock is the single source of
truth; `just sync-versions` repairs drift).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_versions import drift_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    sources = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
    configured = set(sources["packages"])
    recipes = {d.name for d in (ROOT / "pigeon" / "packages").iterdir() if d.is_dir()}
    errors = []
    # Every recipe on disk needs a source entry (allow-list).
    for r in sorted(recipes):
        if r not in configured:
            errors.append(f"recipe without source entry: {r}")
    # Every non-local entry needs a filename matching the rendered URL
    # basename (what fetch --stage-into stages for the build).
    for name in sorted(configured):
        entry = sources["packages"][name]
        if entry.get("local"):
            continue
        url = entry.get("url_template", "").replace("{version}", str(entry.get("version", "")))
        expected = url.rsplit("/", 1)[-1] if "/" in url else ""
        if entry.get("filename") != expected:
            errors.append(
                f"stale filename for {name}: {entry.get('filename')!r} != {expected!r}"
            )
    # Every spec Version: must match the lock (single source of truth).
    for name, spec_ver, lock_ver in drift_for(ROOT / "pigeon" / "packages", sources):
        errors.append(
            f"version drift for {name}: spec {spec_ver!r} != lock {lock_ver!r} "
            f"(run `just sync-versions`)"
        )
    if errors:
        print("\n".join(errors))
        return 1
    print(f"validated {len(configured)} source entries ({len(recipes)} recipes on disk)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
