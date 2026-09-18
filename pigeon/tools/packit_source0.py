#!/usr/bin/env python3
"""Tell Packit to use the factory's already-verified Source0 archive.

If the source is not staged locally, download it from the verified URL,
verify the SHA-512, and return the path.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = REPO_ROOT / "pigeon" / "config" / "upstream-sources.json"


def sha512_of(path: Path) -> str:
    h = hashlib.sha512()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    """Download a URL to a destination file."""
    req = urllib.request.Request(url, headers={"User-Agent": "Kestrel-source-pipeline/1.0"})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def get_or_fetch_source0(root: Path, spec_path: Path, package_name: str, lock: dict, working_directory: Path) -> str:
    """Return path to Source0 archive, downloading if necessary."""
    filename = lock.get("filename")
    if not filename:
        raise ValueError(f"no filename in upstream-sources for {package_name}")

    # Check if already staged locally
    staged = spec_path.parent / lock["filename"]
    if staged.is_file():
        return str(staged.resolve().relative_to(working_directory))

    # Not staged - download from URL, verify, and stage
    url = lock["url_template"].replace("{version}", lock["version"])
    expected_sha512 = lock["sha512"]
    if not expected_sha512 or expected_sha512.startswith("TODO"):
        raise ValueError(f"no recorded digest for {package_name} — run `record {package_name}` first")

    # Download to temp location
    with tempfile.TemporaryDirectory(prefix=f"kestrel-{package_name}-") as tmp:
        workdir = Path(tmp)
        archive = workdir / filename
        print(f"Downloading {package_name} from {url}")
        download(url, archive)

        # Verify SHA-512
        actual_sha512 = sha512_of(archive)
        if actual_sha512 != expected_sha512:
            raise ValueError(f"SHA-512 mismatch for {package_name}: expected {expected_sha512}, got {actual_sha512}")

        # Stage the verified archive in the package directory
        staged = spec_path.parent / filename
        staged.write_bytes(archive.read_bytes())
        print(f"Staged verified source: {staged}")

    return str(staged.resolve().relative_to(working_directory))


def verified_source0(root: Path, working_directory: Path | None = None) -> str:
    spec_path = os.environ.get("PACKIT_SPECFILE_PATH")
    if not spec_path:
        raise ValueError("PACKIT_SPECFILE_PATH is not set")

    configured = Path(spec_path)
    candidates = []
    package_env = os.environ.get("PACKAGE")
    if package_env and (root / "pigeon" / "packages" / package_env / configured.name).is_file():
        candidates.append(root / "pigeon" / "packages" / package_env / configured.name)
    elif configured.is_absolute() and configured.is_file():
        candidates.append(configured)
    elif (root / configured).is_file():
        candidates.append(root / configured)
    else:
        candidates.extend(root.glob(f"pigeon/packages/*/{configured.name}"))

    if len(candidates) != 1:
        raise ValueError(f"cannot uniquely locate Packit spec file: {spec_path}")

    package_name = candidates[0].parent.name

    # Load upstream-sources.json for the source lock
    locks = json.loads((root / "pigeon" / "config" / "upstream-sources.json").read_text())
    lock = locks["packages"].get(candidates[0].parent.name)
    if lock is None:
        raise ValueError(f"no upstream-sources entry for {candidates[0].parent.name}")

    # For packages with local sources, look for the verified archive
    if lock.get("local"):
        raise ValueError(f"package {package_name} is local, no Source0")

    filename = lock.get("filename")
    if not filename:
        raise ValueError(f"no filename in upstream-sources for {package_name}")

    working_directory = (working_directory or Path.cwd()).resolve()
    return get_or_fetch_source0(root, candidates[0], candidates[0].parent.name, locks["packages"][candidates[0].parent.name], working_directory)


def main() -> int:
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    )
    print(verified_source0(root, Path.cwd()))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error