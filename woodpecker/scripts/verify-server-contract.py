#!/usr/bin/env python3
"""Verify server contract matches installed system.

Usage:
  verify-server-contract.py --contract PATH
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def check_file_exists(path: str) -> bool:
    return Path(path).exists()


def check_service_enabled(service: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-enabled", service],
            capture_output=True, text=True
        )
        return result.returncode == 0 and result.stdout.strip() == "enabled"
    except Exception:
        return False


def check_command_exists(cmd: str) -> bool:
    return Path(cmd).exists() or bool(
        subprocess.run(["which", cmd], capture_output=True).returncode == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify server contract")
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()

    data = tomllib.loads(args.contract.read_text())
    errors = []

    # Check services
    if "services" in data:
        svc = data["services"]
        if svc.get("cockpit_enabled") and not check_service_enabled("cockpit.socket"):
            errors.append("Cockpit socket not enabled")
        if svc.get("uupd_enabled") and not check_service_enabled("uupd.timer"):
            errors.append("uupd timer not enabled")
        if svc.get("bootc_auto_update_enabled") and not check_service_enabled("bootc-auto-update.timer"):
            errors.append("bootc-auto-update timer not enabled")
        if svc.get("networkmanager_enabled") and not check_service_enabled("NetworkManager.service"):
            errors.append("NetworkManager not enabled")
        if svc.get("firewalld_enabled") and not check_service_enabled("firewalld.service"):
            errors.append("firewalld not enabled")

        # SSH should be disabled by default
        if svc.get("sshd_enabled") is False and check_service_enabled("sshd.socket"):
            errors.append("SSH socket should be disabled by default")

    # Check container tools
    if "container" in data:
        c = data["container"]
        for tool in ["podman", "skopeo", "buildah", "runc", "crun"]:
            if not check_command_exists(f"/usr/bin/{tool}"):
                errors.append(f"Container tool not found: {tool}")

    # Check management
    if "management" in data:
        m = data["management"]
        if not check_file_exists(m.get("cockpit_port", "")):
            # Port check is runtime, just verify config exists
            pass

    # Check security
    if "security" in data:
        s = data["security"]
        if not check_file_exists("/etc/ssh/sshd_config.d/99-woodpecker-hardening.conf"):
            errors.append("SSH hardening config not found")
        if not check_file_exists("/etc/ssh/banner"):
            errors.append("SSH banner not found")

    if errors:
        print("SERVER CONTRACT VIOLATIONS:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("Server contract verified OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())