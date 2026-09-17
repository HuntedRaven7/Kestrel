"""Emit package list for packit-srpm-pilot.yml.

Usage: packit_workflow.py packages   -> JSON list on stdout
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def packages() -> list[str]:
    data = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
    return sorted(data["packages"])


def main(argv: list[str]) -> int:
    if argv != ["packages"]:
        print(f"usage: {Path(sys.argv[0]).name} packages", file=sys.stderr)
        return 2
    print(json.dumps(packages()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
