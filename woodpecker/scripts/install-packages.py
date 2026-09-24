#!/usr/bin/env python3
"""Install packages from RPM factory repo + base image per woodpecker.toml contract.

Usage:
  install-packages.py --contract PATH --repo PATH --base-image IMAGE
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def parse_contract(path: Path) -> dict[str, str]:
    """Parse woodpecker.toml and return {package: version_or_wildcard}."""
    data = tomllib.loads(path.read_text())
    pkgs = {}
    for section in ("woodpecker",):
        if section in data:
            pkgs.update(data[section])
    return pkgs


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Woodpecker packages")
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--base-image", required=True)
    args = parser.parse_args()

    pkgs = parse_contract(args.contract)
    if not pkgs:
        print("ERROR: No packages in contract", file=sys.stderr)
        return 1

    # Build repo config for RPM factory repo
    repo_file = Path("/etc/yum.repos.d/rpm-factory.repo")
    repo_file.write_text(f"""[rpm-factory]
name=Kestrel RPM Factory
baseurl=file://{args.repo}
enabled=1
gpgcheck=0
priority=5
""")

    # Filter out wildcard versions (from base) - they'll be installed from base repos
    factory_pkgs = [f"{name}-{ver}" if ver != "*" else name for name, ver in pkgs.items() if ver != "*"]
    base_pkgs = [name for name, ver in pkgs.items() if ver == "*"]

    # Install from RPM factory repo
    if factory_pkgs:
        print(f"Installing from RPM factory repo: {factory_pkgs}")
        subprocess.run(
            ["dnf", "install", "-y", "--repo=rpm-factory", *factory_pkgs],
            check=True,
        )

    # Install base packages (wildcards) - these come from base image / Fedora repos
    if base_pkgs:
        print(f"Installing from base repos: {base_pkgs}")
        subprocess.run(
            ["dnf", "install", "-y", *base_pkgs],
            check=True,
        )

    print("Package installation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())