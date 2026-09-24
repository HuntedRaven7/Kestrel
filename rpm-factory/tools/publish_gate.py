#!/usr/bin/env python3
"""Fail-closed validation for an assembled rpm-factory repository."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "rpm-factory" / "config" / "tine-packages.json"
RPM_QUERY = "%{NAME}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\n"
ALLOWED_ARCHITECTURES = {"x86_64", "noarch", "src"}


def publish_allowed(*, build_ok: bool, repository_ok: bool) -> bool:
    return bool(build_ok and repository_ok)


def _rpm_record(path: Path) -> tuple[str, str, str, str]:
    output = subprocess.check_output(
        ["rpm", "-qp", "--qf", RPM_QUERY, str(path)],
        text=True,
    ).strip()
    fields = output.split("\t")
    if len(fields) != 4 or not all(fields):
        raise ValueError(f"unexpected RPM metadata in {path}: {output!r}")
    return fields[0], fields[1], fields[2], fields[3]


def check_repository(
    repo_root: Path,
    metadata_path: Path = DEFAULT_METADATA,
    suffix: str = ".hum1.rpmfactory",
) -> bool:
    """Require a complete, readable, correctly tagged set of Tine outputs."""
    metadata = json.loads(metadata_path.read_text())
    expected = {
        name
        for package in metadata["packages"].values()
        for name in [package["package"], *package["subpackages"]]
    }
    rpms = sorted(repo_root.rglob("*.rpm"))
    if not rpms:
        print("[repository] no RPMs found")
        return False

    records: list[tuple[str, str, str, str]] = []
    validated: list[tuple[tuple[str, str, str, str], Path]] = []
    errors: list[str] = []
    for path in rpms:
        try:
            record = _rpm_record(path)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            errors.append(f"unreadable RPM {path.name}: {error}")
            continue
        records.append(record)
        validated.append((record, path))
        name, _version, release, arch = record
        is_source = path.name.endswith(".src.rpm")
        if not release.endswith(suffix):
            errors.append(f"{path.name}: release {release!r} lacks {suffix}")
        if arch not in ALLOWED_ARCHITECTURES:
            errors.append(f"{path.name}: unsupported architecture {arch!r}")
        base = name.removesuffix("-debuginfo").removesuffix("-debugsource")
        if name not in expected and base not in expected:
            errors.append(f"{path.name}: package {name!r} is absent from generated metadata")

    identities = [
        (*record, path.name.endswith(".src.rpm"))
        for record, path in validated
    ]
    if len(identities) != len(set(identities)):
        errors.append("duplicate RPM name/version/release/architecture tuples")

    binary_names = {
        record[0]
        for record, path in validated
        if not path.name.endswith(".src.rpm")
        and record[3] != "src"
        and not record[0].endswith(("-debuginfo", "-debugsource"))
    }
    missing = sorted(expected - binary_names)
    if missing:
        errors.append("missing expected binary RPMs: " + ", ".join(missing))

    if errors:
        for error in errors:
            print(f"[repository] {error}", file=sys.stderr)
        return False
    print(
        f"[repository] verified {len(rpms)} RPMs for "
        f"{len(expected)} expected package names"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--rpm-factory-suffix", required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        print(f"ERROR: {repo_root} does not exist", file=sys.stderr)
        return 1
    allowed = publish_allowed(
        build_ok=True,
        repository_ok=check_repository(
            repo_root,
            args.metadata.resolve(),
            args.rpm_factory_suffix,
        ),
    )
    if allowed:
        print("GATE: PASS")
        return 0
    print("GATE: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
