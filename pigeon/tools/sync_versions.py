#!/usr/bin/env python3
"""Sync recipe spec Version: lines from upstream-sources.json.

The lock file is the single source of truth for versions (Renovate bumps
it); this tool carries each version into its recipe's spec so the two can
never drift apart (cf. polkit shipping 127 while the lock still said 124).

Specs stay plain Fedora-style files on purpose: no macro indirection, so
they still parse standalone in Mock, Copr, or a bare `rpmspec -q` — the
sync is a mechanical rewrite, not a build-time dependency.

Usage:
  sync_versions.py [--check] [--package PKG]

  (no flags)   write lock versions into specs, reporting each change
  --check      report drift without writing (CI gate; exit 1 on drift)
  --package    scope to one recipe dir
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "pigeon" / "config" / "upstream-sources.json"
PKGS = ROOT / "pigeon" / "packages"

VERSION_RE = re.compile(r"^(Version:\s*)(\S+)(\s*)$", re.M)


def parse_spec_version(spec: Path) -> str | None:
    """Return the literal Version: value, or None when absent or macroized
    (a generated version cannot be compared statically)."""
    m = VERSION_RE.search(spec.read_text())
    if not m or "%" in m.group(2):
        return None
    return m.group(2)


def drift_for(packages_root: Path, data: dict) -> list[tuple[str, str, str]]:
    """[(package, spec_version, lock_version)] for every recipe whose spec
    Version: disagrees with the lock. Local entries and recipes without a
    spec are skipped; macroized versions cannot be compared statically."""
    out = []
    for pkgdir in sorted(packages_root.iterdir()):
        if not pkgdir.is_dir():
            continue
        specs = list(pkgdir.glob("*.spec"))
        if not specs:
            continue
        entry = data.get("packages", {}).get(pkgdir.name)
        if not entry or entry.get("local"):
            continue
        lock_ver = str(entry.get("version", ""))
        if not lock_ver or lock_ver.startswith("TODO"):
            continue
        spec_ver = parse_spec_version(specs[0])
        if spec_ver is None:
            continue
        if spec_ver != lock_ver:
            out.append((pkgdir.name, spec_ver, lock_ver))
    return out


def sync_package(pkgdir: Path, lock_ver: str) -> bool:
    """Rewrite the spec's Version: line to the lock version. Returns True
    when the file changed."""
    spec = next(iter(sorted(pkgdir.glob("*.spec"))))
    text = spec.read_text()
    new, n = VERSION_RE.subn(rf"\g<1>{lock_ver}\g<3>", text, count=1)
    if n and new != text:
        spec.write_text(new)
        return True
    return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Sync spec versions from the lock")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--package", "-p", default=None)
    args = ap.parse_args(argv)
    data = json.loads(SOURCES.read_text())
    if args.package and args.package not in {
            d.name for d in PKGS.iterdir() if d.is_dir()}:
        print(f"no recipe dir for package: {args.package}")
        return 2
    # drift_for always walks PKGS; filter afterwards.
    drift = [d for d in drift_for(PKGS, data)
             if args.package is None or d[0] == args.package]
    if args.check:
        for name, spec_ver, lock_ver in drift:
            print(f"version drift for {name}: spec {spec_ver!r} != lock {lock_ver!r}")
        if drift:
            print("run `just sync-versions` (or sync_versions.py) to fix")
            return 1
        print(f"versions in sync ({len(data['packages'])} lock entries checked)")
        return 0
    changed = 0
    for name, _spec_ver, lock_ver in drift:
        if sync_package(PKGS / name, lock_ver):
            print(f"synced {name} -> {lock_ver}")
            changed += 1
    print(f"{changed} spec(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
