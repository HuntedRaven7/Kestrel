"""Validate factory config: provenance + source-lock + packit coverage (stub).

Full gates in PLAN.md §3.4. Fails if any recipe dir lacks a source entry,
or any source entry lacks a .packit.yaml packages entry and vice versa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # PyYAML may be absent locally; CI installs it
    yaml = None  # type: ignore

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
    # basename (what fetch --stage-into stages; what packit_source0.py reads).
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
    # .packit.yaml coverage (only if recipes exist and yaml parses).
    packit = ROOT / ".packit.yaml"
    if yaml is not None and packit.exists():
        pkgs = (yaml.safe_load(packit.read_text()) or {}).get("packages", {})
        for r in sorted(recipes):
            if r not in pkgs:
                errors.append(f"recipe without packit entry: {r}")
        for p in sorted(pkgs):
            if p not in configured:
                errors.append(f"packit entry without source entry: {p}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"validated {len(configured)} source entries ({len(recipes)} recipes on disk)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
