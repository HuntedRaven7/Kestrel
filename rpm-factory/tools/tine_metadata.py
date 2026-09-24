#!/usr/bin/env python3
"""Generate and verify the rpm-factory Buck2 package graph.

The source lock and the RPM specs remain authoritative.  This file only projects
those inputs into the small amount of metadata Tine's rpm.package rule needs:
the evaluated BuildRequires, output subpackages, release base, and a stable
SOURCE_DATE_EPOCH.  Regenerate it in a Fedora 46 box after changing a spec.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import timezone
from functools import lru_cache
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTORY = ROOT / "rpm-factory"
CONTRACT = json.loads((FACTORY / "config" / "factory-contract.json").read_text())
DIST = CONTRACT["rpm_suffix"]
CHUNK_SIZE = 5
METADATA = FACTORY / "config" / "tine-packages.json"
DYNAMIC = FACTORY / "config" / "tine-dynamic-buildrequires.json"
BUCK = FACTORY / "BUCK"
TARGET_NAME = re.compile(r"^[A-Za-z0-9_.+-]+$")
DYNAMIC_REQUIREMENTS = json.loads(DYNAMIC.read_text()) if DYNAMIC.is_file() else {}


def _run(command: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def _rpmspec(spec: Path, arguments: list[str], *, parsed: bool = False) -> str:
    command = ["rpmspec", "--target", "x86_64"]
    if not parsed:
        command.append("-q")
    command.extend(arguments)
    command.extend(
        [
            "--define",
            f"_sourcedir {spec.parent.resolve()}",
            "--define",
            f"dist {DIST}",
            str(spec),
        ]
    )
    return _run(command)


@lru_cache(maxsize=1)
def _staged_renames() -> dict[str, str]:
    """Map staged destination paths to their pre-rename history paths."""
    changes = _run(
        ["git", "diff", "--cached", "--name-status", "--find-renames=50%"]
    )
    result: dict[str, str] = {}
    for line in changes.splitlines():
        fields = line.split("\t")
        if len(fields) == 3 and fields[0].startswith("R"):
            result[fields[2]] = fields[1]
    return result


def _source_date_epoch(spec: Path) -> int:
    dates = re.findall(r"^%date\s+(.+?)\s*$", spec.read_text(), re.IGNORECASE | re.MULTILINE)
    for value in reversed(dates):
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(1, int(parsed.timestamp()))
    relative = str(spec.relative_to(ROOT))
    candidates = (relative, _staged_renames().get(relative))
    for candidate in candidates:
        if not candidate:
            continue
        committed = _run(
            ["git", "log", "--follow", "-1", "--format=%ct", "--", candidate]
        ).strip()
        if committed:
            return max(1, int(committed))
    return 1


def _target_name(directory: str) -> str:
    if not TARGET_NAME.fullmatch(directory):
        raise ValueError(f"package directory is not a Buck target name: {directory!r}")
    return directory


def _subpackages(spec: Path) -> list[str]:
    built = {
        line.strip()
        for line in _rpmspec(spec, ["--builtrpms", "--queryformat", "%{NAME}\n"]).splitlines()
        if line.strip()
    }
    raw = spec.read_text()
    declared: set[str] = set()
    parsed: set[str] = set()
    for match in re.finditer(r"^%package(?:\s+-n)?\s+([^\s]+)", raw, re.MULTILINE):
        declared.add(match.group(1).strip("'").strip('"'))
    for line in raw.splitlines():
        if not line.startswith("%pyproject_extras_subpkg "):
            continue
        fields = line.split()
        try:
            name_index = fields.index("-n") + 1
        except ValueError:
            continue
        base = fields[name_index]
        parsed.update(base + "+" + extra for extra in fields[1:name_index - 1])
    for line in _rpmspec(spec, ["-P"], parsed=True).splitlines():
        match = re.match(r"^%package(?:\s+-n)?\s+([^\s]+)", line)
        if match:
            parsed.add(match.group(1).strip("'").strip('"'))
    # Macro-generated packages (not textually declared in the spec) need the
    # parsed form; ordinary conditional declarations are left to --builtrpms.
    result = built | (parsed - declared)
    return sorted(name for name in result if not name.endswith(("-debuginfo", "-debugsource")))


def _package_record(directory: Path) -> dict:
    specs = sorted(directory.glob("*.spec"))
    if len(specs) != 1:
        raise ValueError(f"{directory}: expected exactly one spec, found {len(specs)}")
    spec = specs[0]
    fields = _rpmspec(spec, ["--queryformat", "%{NAME}\n%{VERSION}\n%{RELEASE}\n"])
    field_lines = fields.splitlines()
    if len(field_lines) < 3:
        raise ValueError(f"{spec}: rpmspec returned incomplete identity fields")
    package = field_lines[0]
    release = field_lines[2]
    if release.endswith(DIST):
        release = release[: -len(DIST)]
    if not release:
        raise ValueError(f"{spec}: empty release after removing {DIST}")
    build_requires = {
        line.strip()
        for line in _rpmspec(spec, ["--buildrequires"]).splitlines()
        if line.strip() and not line.startswith("rpmlib(")
    }
    build_requires.update(DYNAMIC_REQUIREMENTS.get(directory.name, []))
    build_requires = sorted(build_requires)
    subpackages = _subpackages(spec)
    if not subpackages:
        raise ValueError(f"{spec}: rpmspec produced no binary subpackages")
    return {
        "target": _target_name(directory.name),
        "package": package,
        "spec": str(spec.relative_to(FACTORY)),
        "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
        "recipe_dir": str(directory.relative_to(FACTORY)),
        "release": release,
        "dist": DIST,
        "source_date_epoch": _source_date_epoch(spec),
        "build_requires": build_requires,
        "subpackages": subpackages,
        "rpmbuild_options": [],
    }


def _metadata() -> dict:
    lock = json.loads((FACTORY / "config" / "upstream-sources.json").read_text())["packages"]
    packages: dict[str, dict] = {}
    for directory in sorted((FACTORY / "packages").iterdir()):
        if not directory.is_dir():
            continue
        if directory.name not in lock:
            raise ValueError(f"recipe without source-lock entry: {directory.name}")
        record = _package_record(directory)
        record["source_lock_sha512"] = lock[directory.name].get("sha512")
        packages[record["target"]] = record
    if not packages:
        raise ValueError("no buildable rpm-factory packages found")
    names = sorted(packages)
    chunks = [names[index : index + CHUNK_SIZE] for index in range(0, len(names), CHUNK_SIZE)]
    return {
        "schema": 1,
        "build_system": CONTRACT["build_system"],
        "tine_commit": CONTRACT["tine_commit"],
        "fedora": "rawhide",
        "fedora_release": CONTRACT["fedora_baseline"],
        "dist": DIST,
        "chunk_size": CHUNK_SIZE,
        "chunks": chunks,
        "packages": packages,
    }


def _buck(metadata: dict) -> str:
    def quote(value: str) -> str:
        return json.dumps(value)

    def string_list(values: list[str]) -> str:
        return "[" + ", ".join(quote(value) for value in values) + "]"

    lines = [
        "# @generated by rpm-factory/tools/tine_metadata.py; do not edit.",
        'load("@prelude//:native.bzl", "native")',
        'load("@tine//package_system/rpm:defs.bzl", "rpm")',
        "",
        '_BUILDROOT = "//rpm-factory/buildroots:f46"',
        "",
    ]
    for target, config in sorted(metadata["packages"].items()):
        lines.extend(
            [
                "rpm.package(",
                f"    name = {quote(target)},",
                f"    package = {quote(config['package'])},",
                f"    spec = {quote(config['spec'])},",
                "    srcs = native.glob(",
                f"        [{quote('.tine-sources/' + target + '/*')}],",
                "    ),",
                f"    buildroot = _BUILDROOT,",
                f"    release = {quote(config['release'])},",
                f"    dist = {quote(config['dist'])},",
                f"    source_date_epoch = {config['source_date_epoch']},",
                f"    build_requires = {string_list(config['build_requires'])},",
                f"    rpmbuild_options = {string_list(config['rpmbuild_options'])},",
                f"    subpackages = {string_list(config['subpackages'])},",
                ")",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated metadata and BUCK")
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args(argv)
    metadata = _metadata()
    rendered_metadata = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    rendered_buck = _buck(metadata)
    if args.write:
        METADATA.write_text(rendered_metadata)
        BUCK.write_text(rendered_buck)
        print(f"wrote {METADATA.relative_to(ROOT)} and {BUCK.relative_to(ROOT)}")
        return 0
    if args.check:
        stale = []
        for path, rendered in ((METADATA, rendered_metadata), (BUCK, rendered_buck)):
            if not path.is_file() or path.read_text() != rendered:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            print("stale generated Tine metadata: " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"Tine metadata is current ({len(metadata['packages'])} packages)")
        return 0
    print(rendered_metadata, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
