#!/usr/bin/env python3
"""Validate .packit.yaml matches upstream-sources.json.

Ensures:
- No rpmbuild/local packages in .packit.yaml
- All non-rpmbuild packages with specs are in .packit.yaml
"""
import json
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKIT_YAML = ROOT / ".packit.yaml"
SOURCES_JSON = ROOT / "pigeon" / "config" / "upstream-sources.json"
PKGS_DIR = ROOT / "pigeon" / "packages"


def main() -> int:
    with open(SOURCES_JSON) as f:
        sources = json.load(f)

    with open(PACKIT_YAML) as f:
        packit = yaml.safe_load(f)

    # Find rpmbuild/local packages
    rpmbuild = {name for name, entry in sources["packages"].items()
                if entry.get("srpm") == "rpmbuild" or entry.get("local")}

    # Find packages with recipe dirs
    has_spec = {d.name for d in PKGS_DIR.iterdir() if d.is_dir()
                and list(d.glob("*.spec"))}

    packit_packages = set(packit["packages"].keys())

    errors = []

    # Check: rpmbuild packages should NOT be in .packit.yaml
    in_packit = rpmbuild & packit_packages
    if in_packit:
        errors.append(f"rpmbuild/local packages in .packit.yaml: {sorted(in_packit)}")

    # Check: non-rpmbuild packages with specs SHOULD be in .packit.yaml
    should_be_in_packit = has_spec - rpmbuild
    missing = should_be_in_packit - packit_packages
    if missing:
        errors.append(f"packages with specs missing from .packit.yaml: {sorted(missing)}")

    # Check: packages in .packit.yaml should have specs
    extra = packit_packages - has_spec
    if extra:
        errors.append(f"packages in .packit.yaml without spec dir: {sorted(extra)}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"OK: .packit.yaml valid ({len(packit_packages)} packages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())