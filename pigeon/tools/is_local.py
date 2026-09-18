#!/usr/bin/env python3
"""Exit 0 when the source entry is a local (file-only) package.

Used by CI to route local packages to plain `rpmbuild -bs` instead of
`packit srpm` (there is no upstream archive for create_archive to make).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(f"usage: {Path(sys.argv[0]).name} <package>", file=sys.stderr)
        return 2
    data = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
    entry = data["packages"].get(argv[0], {})
    return 0 if entry.get("local") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
