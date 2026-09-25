#!/usr/bin/env python3
# SPDX-FileCopyrightText: Kestrel contributors
# SPDX-License-Identifier: Apache-2.0
"""Plan the Tine package matrix from the generated package projection.

The workflow and local ``just matrix`` command use this one planner so a
partial-selection build cannot silently diverge from the chunk definition
committed in ``tine-packages.json``.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "rpm-factory" / "config" / "tine-packages.json"


def _package_names(metadata: dict[str, Any]) -> list[str]:
    packages = metadata.get("packages")
    if not isinstance(packages, dict) or not packages:
        raise ValueError("Tine metadata has no packages")
    return sorted(packages)


def _selected_names(requested: str, all_names: list[str]) -> list[str]:
    if not requested.strip():
        return all_names
    selected = {name for name in re.split(r"[\s,]+", requested.strip()) if name}
    unknown = sorted(selected - set(all_names))
    if unknown:
        raise ValueError("unknown package(s): " + ", ".join(unknown))
    return [name for name in all_names if name in selected]


def _validate_chunks(chunks: Any, names: list[str]) -> None:
    if not isinstance(chunks, list):
        raise ValueError("Tine metadata chunks must be a list")
    flattened: list[str] = []
    for chunk in chunks:
        if not isinstance(chunk, list) or not all(isinstance(name, str) for name in chunk):
            raise ValueError("Tine metadata contains a malformed chunk")
        flattened.extend(chunk)
    if flattened != names:
        raise ValueError("generated chunks do not exactly cover the selected package set")


def plan(metadata: dict[str, Any], requested: str = "") -> dict[str, Any]:
    """Return a validated matrix plan for a package selection."""
    all_names = _package_names(metadata)
    names = _selected_names(requested, all_names)
    if requested.strip():
        chunk_size = metadata.get("chunk_size")
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("Tine metadata has an invalid chunk_size")
        chunks = [names[index:index + chunk_size] for index in range(0, len(names), chunk_size)]
        complete = set(names) == set(all_names)
    else:
        chunks = metadata.get("chunks")
        _validate_chunks(chunks, names)
        complete = True

    matrix = [
        {"index": index, "packages": " ".join(chunk)}
        for index, chunk in enumerate(chunks)
    ]
    return {
        "chunks": chunks,
        "complete": complete,
        "matrix": matrix,
        "package_count": len(names),
    }


def _write_github_output(plan_result: dict[str, Any], output: Path) -> None:
    with output.open("a") as stream:
        stream.write("matrix=" + json.dumps(plan_result["matrix"], separators=(",", ":")) + "\n")
        stream.write(f"package-count={plan_result['package_count']}\n")
        stream.write(f"complete={str(plan_result['complete']).lower()}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--requested", default=os.environ.get("PACKAGES", ""))
    parser.add_argument("--output", type=Path, default=Path(os.environ["GITHUB_OUTPUT"])
                        if os.environ.get("GITHUB_OUTPUT") else None)
    parser.add_argument("--json", action="store_true", help="print the plan as JSON")
    args = parser.parse_args(argv)

    try:
        metadata = json.loads(args.metadata.read_text())
        result = plan(metadata, args.requested)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"matrix planning failed: {exc}", file=sys.stderr)
        return 1

    if args.output is not None:
        _write_github_output(result, args.output)
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(
            f"prepared {result['package_count']} package(s) in "
            f"{len(result['matrix'])} chunk(s); complete={str(result['complete']).lower()}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
