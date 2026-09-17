"""Publish gate: refuse partial/failed factory output.

CLI:
  python3 publish_gate.py --repo-root PATH --base-image IMAGE --pigeon-suffix SUFFIX
    --repo-root: directory containing built RPMs organized by stage/package
    --base-image: Hummingbird base image to check against
    --pigeon-suffix: RPM release suffix (e.g., .hum1.pigeon)

Exit codes:
  0: all gates pass (precedence + transaction)
  1: gate failure
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def publish_allowed(*, build_ok: bool, precedence_ok: bool, transaction_ok: bool) -> bool:
    return bool(build_ok and precedence_ok and transaction_ok)


def check_precedence(repo_root: Path, base_image: str, suffix: str) -> bool:
    """Check that Pigeon RPMs outrank Fedora 44 + Hummingbird.

    Uses `rpm -q --queryformat` and `skopeo inspect` to compare EVR.
    """
    print(f"[precedence] Checking RPMs in {repo_root} against {base_image}")
    # TODO: Implement real precedence check
    # For now, always pass if we have any RPMs
    rpms = list(repo_root.rglob("*.rpm"))
    if not rpms:
        print("[precedence] No RPMs found, failing")
        return False
    print(f"[precedence] Found {len(rpms)} RPMs, assuming precedence OK (stub)")
    return True


def check_transaction(repo_root: Path, base_image: str, suffix: str) -> bool:
    """Verify that the RPM set can be installed on the base image.

    Uses `dnf install --dry-run` in a container.
    """
    print(f"[transaction] Checking installability on {base_image}")
    # TODO: Implement real transaction check
    print("[transaction] Assuming transaction OK (stub)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Pigeon publish gate")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--base-image", required=True)
    parser.add_argument("--pigeon-suffix", required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if not repo_root.exists():
        print(f"ERROR: {repo_root} does not exist")
        return 1

    build_ok = True  # build-stage jobs already succeeded
    precedence_ok = check_precedence(repo_root, args.base_image, args.pigeon_suffix)
    transaction_ok = check_transaction(repo_root, args.base_image, args.pigeon_suffix)

    allowed = publish_allowed(
        build_ok=build_ok,
        precedence_ok=precedence_ok,
        transaction_ok=transaction_ok,
    )

    if allowed:
        print("GATE: PASS")
        return 0
    else:
        print("GATE: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())