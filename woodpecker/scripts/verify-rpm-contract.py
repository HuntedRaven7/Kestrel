#!/usr/bin/env python3
"""Verify installed RPMs match woodpecker.toml contract.

Usage:
  verify-rpm-contract.py --contract PATH --installed-db PATH
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def parse_contract(path: Path) -> dict[str, str]:
    data = tomllib.loads(path.read_text())
    pkgs = {}
    for section in ("woodpecker",):
        if section in data:
            pkgs.update(data[section])
    return pkgs


def get_installed_rpms(dbpath: str | None = None) -> dict[str, str]:
    """Query RPM database for installed packages."""
    cmd = ["rpm", "-qa", "--queryformat", "%{NAME} %{VERSION}-%{RELEASE}\\n"]
    if dbpath:
        cmd.extend(["--dbpath", dbpath])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    installed = {}
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                installed[parts[0]] = parts[1]
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify RPM contract")
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--installed-db", required=True, type=Path)
    args = parser.parse_args()

    expected = parse_contract(args.contract)
    installed = get_installed_rpms(str(args.installed_db))

    missing = []
    version_mismatch = []

    for name, expected_ver in expected.items():
        if expected_ver == "*":
            # Wildcard - just check package exists
            if name not in installed:
                missing.append(name)
        else:
            # Exact version match (allow release suffix flexibility)
            if name not in installed:
                missing.append(f"{name} (expected {expected_ver})")
            else:
                installed_ver = installed[name]
                # Compare version part (before release)
                exp_version = expected_ver.split("-")[0]
                inst_version = installed_ver.split("-")[0]
                if exp_version != inst_version:
                    version_mismatch.append(
                        f"{name}: expected {exp_version}, got {inst_version}"
                    )

    if missing:
        print("MISSING packages:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)

    if version_mismatch:
        print("VERSION MISMATCH:", file=sys.stderr)
        for v in version_mismatch:
            print(f"  {v}", file=sys.stderr)

    if missing or version_mismatch:
        return 1

    print("RPM contract verified OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())