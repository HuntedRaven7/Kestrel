"""Emit package list for packit-srpm-pilot.yml.

Usage: packit_workflow.py packages   -> JSON list on stdout
       packit_workflow.py chunks     -> JSON list of chunked JSON arrays
"""
from __future__ import annotations

import argparse
import json
import re
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


# GitHub caps a matrix at 256 jobs, and a larger one does not fail -- it
# expands to nothing. The pilot enumerates every package in the monorepo, so
# once that passed 256 its srpm matrix produced zero jobs and the run failed
# beneath a green discover step. Hand the matrix chunks instead.
MATRIX_CHUNK = 250


def package_chunks(names: list[str], size: int = MATRIX_CHUNK) -> list[str]:
    """Split names into JSON-encoded chunks, none exceeding the matrix cap."""
    if size < 1:
        raise ValueError("chunk size must be positive")
    return [
        json.dumps(names[start : start + size])
        for start in range(0, len(names), size)
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("packages")

    chunks = sub.add_parser("chunks")
    chunks.add_argument("--size", type=int, default=MATRIX_CHUNK)

    args = parser.parse_args(argv)
    if args.command == "packages":
        print(json.dumps(packages()))
    elif args.command == "chunks":
        print(json.dumps(package_chunks(packages(), args.size)))
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))