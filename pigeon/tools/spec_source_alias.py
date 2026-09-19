#!/usr/bin/env python3
"""Link the staged primary archive under spec Source0 basenames.

Fedora specs reference lookaside-renamed tarballs (e.g.
`libblockdev-3.5.0.tar.gz`) while upstream URLs serve tag-named files
(e.g. `3.5.0.tar.gz`). The packit SRPM lane bridges this via the
create_archive positional Source0 override; raw rpmbuild (the build-stage
lane) needs the spec's basename present in SOURCES.

Usage:
  spec_source_alias.py --spec SPEC --sources DIR --staged FILE

For every Source0-position entry (Source/Source0 tags) whose basename is
missing from DIR, hardlink FILE to DIR/basename (copy fallback). Secondary
sources (Source1+) are deliberately left alone so genuinely-missing inputs
still fail loudly in rpmbuild. Unresolvable macro basenames are skipped.
Never fails: reports what it did, exits 0.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_sources import expand, parse_spec  # noqa: E402


def alias_source0(spec: Path, sources: Path, staged: Path,
                   recipe_dir: Path | None = None) -> list[str]:
    """Create missing Source0-basename links. Returns list of created names."""
    macros, checks, _topdir = parse_spec(spec)
    # Fedora idiom `%{!?version_no_tilde: %define ...}`: default to Version
    # with ~ mapped to - (covers nvme-cli/podman-style dynamic macros that
    # static expansion cannot evaluate).
    macros.setdefault("version_no_tilde", macros.get("version", "").replace("~", "-"))
    text = spec.read_text()
    # parse_spec drops the first Source; re-derive Source0-position tags here
    # (including conditional duplicates like libinput's snapshot/release pair).
    import re

    first_tags: list[str] = []
    for m in re.finditer(r"^(Source\d*|Patch\d*)\s*:\s*(\S+)", text, re.M):
        tag, raw = m.group(1), m.group(2)
        if tag in ("Source", "Source0"):
            first_tags.append(raw)
    created = []
    for raw in first_tags:
        base = expand(raw, macros).rsplit("/", 1)[-1]
        if "%{" in base or not base:
            print(f"  skip unresolvable Source0: {raw}")
            continue
        if base == staged.name:
            continue
        # A file the recipe already provides (services, keys, .sig files)
        # must never be shadowed by a tarball alias.
        if recipe_dir is not None and (recipe_dir / base).is_file():
            continue
        dest = sources / base
        if dest.exists():
            continue
        try:
            os.link(staged, dest)
        except OSError:
            shutil.copy2(staged, dest)
        print(f"  aliased {staged.name} -> {base}")
        created.append(base)
    return created


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Alias staged archive under Source0 names")
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--sources", required=True, type=Path)
    ap.add_argument("--staged", required=True, type=Path)
    ap.add_argument("--recipe-dir", default=None, type=Path,
                    help="recipe dir whose files must never be shadowed")
    args = ap.parse_args(argv)
    if not args.staged.is_file():
        print(f"no staged archive at {args.staged}, nothing to alias")
        return 0
    args.sources.mkdir(parents=True, exist_ok=True)
    alias_source0(args.spec, args.sources, args.staged, args.recipe_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
