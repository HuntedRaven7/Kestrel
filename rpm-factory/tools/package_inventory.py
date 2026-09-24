#!/usr/bin/env python3
"""Repository-wide package inventory for the RPM factory factory.

Every factory task consumes :func:`inventory` instead of rescanning
``packages/`` or ``config/upstream-sources.json`` on its own. The lock file
is parsed exactly once, here, so duplicate names, unknown stages, or multiple
specs per package are contract violations for every reader, not warnings.

The source lock is ``rpm-factory/config/upstream-sources.json``: a map of
package name -> entry (version, url_template, sha512, filename, ...). This
module adapts that shape to the same PackageRecord consumers expect.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Stages the rebuild matrix (.github/workflows/rebuild-rpm-factory.yml) can resolve.
KNOWN_STAGES = frozenset(range(5))


@dataclass(frozen=True)
class PackageRecord:
    name: str
    spec: Path
    stage: int
    source_locked: bool


def _spec_per_package(root: Path) -> dict[str, Path]:
    specs: dict[str, Path] = {}
    for directory in sorted((root / "rpm-factory" / "packages").iterdir()):
        if not directory.is_dir():
            continue
        found = sorted(directory.glob("*.spec"))
        if len(found) != 1:
            raise ValueError(f"expected exactly one spec in {directory}")
        if directory.name in specs:
            raise ValueError(f"duplicate spec directory: {directory.name}")
        specs[directory.name] = found[0]
    return specs


def load_source_locks(config: Path) -> dict[str, dict]:
    """Validated source-lock entries keyed by package name.

    The only parse of ``upstream-sources.json`` in the factory: a duplicated
    package name or an unknown stage is a contract violation for every reader.
    """
    data = json.loads(config.read_text())
    locks: dict[str, dict] = {}
    for name, entry in data["packages"].items():
        if name in locks:
            raise ValueError(f"duplicate source lock: {name}")
        stage = entry.get("stage", 2)
        if not isinstance(stage, int) or stage not in KNOWN_STAGES:
            raise ValueError(f"unknown stage for {name}: {stage!r}")
        locks[name] = dict(entry)
        locks[name]["stage"] = stage
    return locks


def source_locks(root: Path) -> dict[str, dict]:
    """The validated source locks for the repository at ``root``."""
    return load_source_locks(root / "rpm-factory" / "config" / "upstream-sources.json")


def inventory(root: Path) -> list[PackageRecord]:
    """Every buildable package: recipe dir with exactly one spec.

    Entries without a recipe (spec still TBD) are not returned -- the matrix
    never runs audit or packit on a missing dir.
    """
    specs = _spec_per_package(root)
    locks = load_source_locks(root / "rpm-factory" / "config" / "upstream-sources.json")
    return [
        PackageRecord(
            name=name,
            spec=spec,
            stage=locks[name].get("stage", 2) if name in locks else 2,
            source_locked=name in locks,
        )
        for name, spec in specs.items()
    ]


def package_names(root: Path) -> list[str]:
    """Sorted buildable package names (for .packit.yaml enumeration)."""
    return [r.name for r in inventory(root)]