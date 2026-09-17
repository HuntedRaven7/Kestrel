#!/usr/bin/env python3
"""Verify desktop contract matches installed system.

Usage:
  verify-desktop-contract.py --contract PATH
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def check_file_exists(path: str) -> bool:
    return Path(path).exists()


def check_service_enabled(service: str, user: bool = False) -> bool:
    cmd = ["systemctl", "is-enabled", service]
    if user:
        cmd = ["systemctl", "--user", "is-enabled", service]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() == "enabled"
    except Exception:
        return False


def check_command_exists(cmd: str) -> bool:
    return Path(cmd).exists() or bool(subprocess.run(["which", cmd], capture_output=True).returncode == 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify desktop contract")
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()

    data = tomllib.loads(args.contract.read_text())
    errors = []

    # Check session
    if "session" in data:
        s = data["session"]
        if not check_file_exists(s.get("session_exec", "")):
            errors.append(f"Session executable not found: {s.get('session_exec')}")
        if not check_file_exists(f"/usr/share/wayland-sessions/{s.get('session_name', '')}.desktop"):
            errors.append(f"Session desktop file not found for {s.get('session_name')}")

    # Check compositor
    if "compositor" in data:
        c = data["compositor"]
        if not check_file_exists(c.get("mango_config", "")):
            errors.append(f"Mango config not found: {c.get('mango_config')}")

    # Check services
    if "services" in data:
        svc = data["services"]
        if svc.get("gdm_enabled") and not check_service_enabled("gdm.service"):
            errors.append("GDM service not enabled")
        if svc.get("seatd_enabled") and not check_service_enabled("seatd.service"):
            errors.append("seatd service not enabled")

    # Check graphics
    if "graphics" in data:
        g = data["graphics"]
        # Basic check for mesa
        if not check_file_exists("/usr/lib64/dri/"):
            errors.append("Mesa DRI drivers not found")

    # Check launcher
    if "launcher" in data:
        l = data["launcher"]
        if not check_file_exists(l.get("rofi_theme", "")):
            errors.append(f"Rofi theme not found: {l.get('rofi_theme')}")

    # Check terminal
    if "terminal" in data:
        t = data["terminal"]
        if not check_file_exists(t.get("ghostty_config", "")):
            errors.append(f"Ghostty config not found: {t.get('ghostty_config')}")

    if errors:
        print("DESKTOP CONTRACT VIOLATIONS:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("Desktop contract verified OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())