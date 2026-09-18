"""Emit package list for packit-srpm-pilot.yml.

Usage: packit_workflow.py packages   -> JSON list on stdout
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def packages() -> list[str]:
    """Source entries that are actually buildable: recipe dir with a spec.

    Entries without a recipe (spec still TBD) are skipped with a stderr
    note so the matrix never runs audit/packit on a missing dir.
    """
    data = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
    buildable, skipped = [], []
    for name in sorted(data["packages"]):
        if list((ROOT / "pigeon" / "packages" / name).glob("*.spec")):
            buildable.append(name)
        else:
            skipped.append(name)
    if skipped:
        print(f"skipping packages without recipe dir: {', '.join(skipped)}",
              file=sys.stderr)
    return buildable


def main(argv: list[str]) -> int:
    if argv != ["packages"]:
        print(f"usage: {Path(sys.argv[0]).name} packages", file=sys.stderr)
        return 2
    print(json.dumps(packages()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
