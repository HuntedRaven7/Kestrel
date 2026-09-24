"""Validate factory config: provenance + source-lock + version sync.

Fails if any recipe dir lacks a source entry, if any source entry's
filename no longer matches its rendered URL basename, or if any spec
Version: disagrees with the lock (the lock is the single source of
truth; `just sync-versions` repairs drift).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_versions import drift_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    sources = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())
    configured = set(sources["packages"])
    recipes = {d.name for d in (ROOT / "rpm-factory" / "packages").iterdir() if d.is_dir()}
    errors = []
    projection_path = ROOT / "rpm-factory" / "config" / "tine-packages.json"
    if projection_path.is_file():
        projection = json.loads(projection_path.read_text())
        projected = set(projection.get("packages", {}))
        if projected != recipes:
            errors.append(
                "Tine projection package set differs from recipes: "
                f"missing={sorted(recipes - projected)} extra={sorted(projected - recipes)}"
            )
        if projection.get("dist") != ".hum1.rpmfactory":
            errors.append(f"Tine projection has unexpected dist {projection.get('dist')!r}")
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
        if entry.get("vendored"):
            if not str(entry.get("vendor_url", "")).startswith("https://"):
                errors.append(f"vendored source for {name} needs an HTTPS vendor_url")
            if not re.fullmatch(r"[0-9a-f]{128}", str(entry.get("vendor_sha512", ""))):
                errors.append(f"vendored source for {name} needs a recorded vendor_sha512")
        url = entry.get("url_template", "").replace("{version}", str(entry.get("version", "")))
        expected = url.rsplit("/", 1)[-1] if "/" in url else ""
        if entry.get("filename") != expected:
            errors.append(
                f"stale filename for {name}: {entry.get('filename')!r} != {expected!r}"
            )
    # Every spec Version: must match the lock (single source of truth).
    for name, spec_ver, lock_ver in drift_for(ROOT / "rpm-factory" / "packages", sources):
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
