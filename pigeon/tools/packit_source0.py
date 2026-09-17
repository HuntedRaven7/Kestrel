#!/usr/bin/env python3
"""Tell Packit to use the factory's already-verified Source0 archive.

This mirrors utah-packages/tools/packit_source0.py but adapted for Kestrel's
pigeon/ structure and upstream-sources.json lock file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]


def verified_source0(root: Path, working_directory: Path | None = None) -> str:
    spec_path = os.environ.get("PACKIT_SPECFILE_PATH")
    if not spec_path:
        raise ValueError("PACKIT_SPECFILE_PATH is not set")

    configured = Path(spec_path)
    candidates = []
    package_env = os.environ.get("PACKAGE")
    if package_env and (root / "pigeon" / "packages" / package_env / configured.name).is_file():
        candidates.append(root / "pigeon" / "packages" / package_env / configured.name)
    elif configured.is_absolute() and configured.is_file():
        candidates.append(configured)
    elif (root / configured).is_file():
        candidates.append(root / configured)
    else:
        candidates.extend(root.glob(f"pigeon/packages/*/{configured.name}"))

    if len(candidates) != 1:
        raise ValueError(f"cannot uniquely locate Packit spec file: {spec_path}")

    package_name = candidates[0].parent.name

    # Load upstream-sources.json for the source lock
    locks = json.loads((root / "pigeon" / "config" / "upstream-sources.json").read_text())
    lock = locks["packages"].get(package_name)
    if lock is None:
        raise ValueError(f"no upstream-sources entry for {package_name}")

    # For packages with local sources, look for the verified archive
    if lock.get("local"):
        # Local package - no Source0 needed
        raise ValueError(f"package {package_name} is local, no Source0")

    filename = lock.get("filename")
    if not filename:
        raise ValueError(f"no filename in upstream-sources for {package_name}")

    archive = candidates[0].parent / filename
    if not archive.is_file():
        raise ValueError(f"verified Source0 is not staged: {archive}")

    working_directory = (working_directory or Path.cwd()).resolve()
    try:
        return str(archive.resolve().relative_to(working_directory))
    except ValueError:
        return str(archive.relative_to(root))


def main() -> int:
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    )
    print(verified_source0(root, Path.cwd()))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error