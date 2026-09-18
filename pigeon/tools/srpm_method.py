#!/usr/bin/env python3
"""Print the SRPM build method for a package: `packit` or `rpmbuild`.

- local entries (file-only, no upstream archive for create_archive) use
  plain `rpmbuild -bs` over the committed Sources.
- entries with `"srpm": "rpmbuild"` use plain `rpmbuild -bs` because
  packit's spec parser cannot handle them (e.g. grub2's %ifs over
  system-macros.d macros that only exist inside real buildroots).
- everything else uses `packit srpm`.

Usage: srpm_method.py <package>   # prints one word, always exits 0
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def method(pkg: str) -> str:
    data = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
    entry = data.get("packages", {}).get(pkg, {})
    if entry.get("local"):
        return "rpmbuild"
    if entry.get("srpm") == "rpmbuild":
        return "rpmbuild"
    return "packit"


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(f"usage: {Path(sys.argv[0]).name} <package>", file=sys.stderr)
        return 2
    print(method(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
