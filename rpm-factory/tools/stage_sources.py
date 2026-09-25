#!/usr/bin/env python3
"""Stage verified sources for one or more rpm-factory recipes.

Tine consumes the staged files as ordinary Buck source artifacts.  The existing
SHA-512/signature pipeline remains the trust boundary; this wrapper only adapts
its single-package commands to a chunked Tine build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTORY = ROOT / "rpm-factory"
TOOLS = FACTORY / "tools"
SOURCES = json.loads((FACTORY / "config" / "upstream-sources.json").read_text())["packages"]


def _run(*arguments: str, cwd: Path = ROOT) -> None:
    subprocess.run(list(arguments), cwd=cwd, check=True)


def _verify_locked_source(package: str, path: Path, expected: str) -> None:
    if not expected:
        raise SystemExit(f"{package}: generated source has no recorded SHA-512")
    digest = hashlib.sha512()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise SystemExit(
            f"{package}: generated source SHA-512 mismatch: "
            f"expected {expected}, got {actual}"
        )


def _stage_one(package: str, output_root: Path) -> None:
    entry = SOURCES.get(package)
    if entry is None:
        raise SystemExit(f"no source-lock entry for {package}")
    recipe = FACTORY / "packages" / package
    specs = sorted(recipe.glob("*.spec"))
    if len(specs) != 1:
        raise SystemExit(f"{package}: expected exactly one spec")
    spec = specs[0]
    output = output_root / package
    # Some repositories commit a verified vendored extra in the Tine source
    # tree. Preserve those bytes before refreshing the directory; the source
    # pipeline can then verify and reuse them without a second host archive.
    preserved_vendored: dict[str, bytes] = {}
    if output.is_dir():
        for extra in entry.get("extra_sources", []) or []:
            if not extra.get("vendored") or not extra.get("filename"):
                continue
            candidate = output / extra["filename"]
            if candidate.is_file():
                preserved_vendored[extra["filename"]] = candidate.read_bytes()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for filename, content in preserved_vendored.items():
        (output / filename).write_bytes(content)

    if entry.get("vendored"):
        _run(sys.executable, str(TOOLS / "fetch_vendored.py"), "--package", package)
    _run(sys.executable, str(TOOLS / "audit_sources.py"), "--package", package)

    if not entry.get("local"):
        _run(
            sys.executable,
            str(TOOLS / "source_pipeline.py"),
            "fetch",
            package,
            "--output",
            str(output),
        )
    else:
        filename = str(entry.get("filename", ""))
        if filename:
            source = recipe / filename
            if not source.is_file():
                generator = recipe / "strip.py"
                if not generator.is_file():
                    raise SystemExit(f"{package}: local source is missing and no strip.py exists")
                _run(sys.executable, str(generator), cwd=recipe)
                source = recipe / filename
            if not source.is_file():
                raise SystemExit(f"{package}: strip.py did not produce {filename}")
            _verify_locked_source(package, source, str(entry.get("sha512", "")))
            shutil.copy2(source, output / filename)

    # Some vendored and dist-git sidecars are intentionally ignored in the
    # recipe directory. Copy every committed/generated recipe input into the
    # unignored Tine source tree so Buck can see those files as well. Never
    # replace the just-verified primary archive with a same-named recipe file.
    primary_name = str(entry.get("filename", ""))
    for candidate in recipe.iterdir():
        if (
            not candidate.is_file()
            or candidate.name == spec.name
            or candidate.name == primary_name
        ):
            continue
        shutil.copy2(candidate, output / candidate.name)

    primary = output / primary_name if primary_name else None
    if primary is not None and primary.is_file():
        _run(
            sys.executable,
            str(TOOLS / "spec_source_alias.py"),
            "--spec",
            str(spec),
            "--sources",
            str(output),
            "--staged",
            str(primary),
            "--recipe-dir",
            str(recipe),
        )
    print(f"staged {package} in {output}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", help="package directory names")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("rpm-factory/.tine-sources"),
        help="directory below which per-package source directories are written",
    )
    args = parser.parse_args(argv)
    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)
    for package in args.packages:
        _stage_one(package, output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
