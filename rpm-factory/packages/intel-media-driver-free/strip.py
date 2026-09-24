#!/usr/bin/env python3
"""Create the locked, reproducible free-only Intel media-driver archive."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REMOVE_ALL_KERNELS = False
# A fixed epoch, owner, sort order, and gzip header make the generated source
# independent of the builder account and wall clock. The resulting SHA-512 is
# still enforced by stage_sources.py before the archive reaches Tine.
ARCHIVE_EPOCH = 0


def _version() -> str:
    value = os.environ.get("RPM_FACTORY_VERSION", "")
    if value:
        return value
    spec = (ROOT / "intel-media-driver-free.spec").read_text()
    match = re.search(r"^Version:\s*(\S+)", spec, re.MULTILINE)
    if not match:
        raise SystemExit("could not determine Intel media-driver version")
    return match.group(1)


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _strip_non_free_sources(unpacked: Path) -> None:
    # Descendants sort before parents, so deleting a matching directory cannot
    # leave a later iteration targeting one of its removed children.
    for path in sorted(unpacked.rglob("*"), reverse=True):
        relative_parts = path.relative_to(unpacked).parts
        in_generation = any("gen" in part for part in relative_parts)
        if path.name == "kernel" and in_generation:
            _remove(path)
        elif path.name.startswith("cm_gpucopy_kernel") or path.name == "cmrt_kernel":
            _remove(path)
        elif REMOVE_ALL_KERNELS and path.name == "kernel_free" and in_generation:
            _remove(path)


def main() -> int:
    version = _version()
    archive = ROOT / f"intel-media-{version}.tar.gz"
    output = ROOT / f"intel-media-{version}-free.tar.gz"
    if not archive.is_file():
        url = os.environ.get(
            "RPM_FACTORY_SOURCE_URL",
            f"https://github.com/intel/media-driver/archive/intel-media-{version}.tar.gz",
        )
        print(f"Downloading {url}", flush=True)
        partial = archive.with_name(f".{archive.name}.part")
        request = urllib.request.Request(url, headers={"User-Agent": "rpm-factory/1"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            partial.replace(archive)
        except Exception as error:
            partial.unlink(missing_ok=True)
            raise SystemExit(f"source download failed: {error}") from error

    with tempfile.TemporaryDirectory(prefix="intel-media-driver-") as temporary:
        work = Path(temporary)
        with tarfile.open(archive) as source:
            source.extractall(work, filter="data")
        candidates = [path for path in work.iterdir() if path.is_dir()]
        if len(candidates) != 1:
            raise SystemExit(f"expected one source directory, found {candidates}")
        unpacked = candidates[0]
        _strip_non_free_sources(unpacked)

        # GNU tar's default archive metadata carries the build account and
        # deletion timestamps. Normalize both and stream through gzip -n so
        # repeated runs produce the exact locked bytes.
        tar_command = [
            "tar",
            "--sort=name",
            f"--mtime=@{ARCHIVE_EPOCH}",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--format=gnu",
            "-cf",
            "-",
            "-C",
            str(work),
            unpacked.name,
        ]
        partial = output.with_name(f".{output.name}.part")
        try:
            with partial.open("wb") as stream:
                tar = subprocess.Popen(tar_command, stdout=subprocess.PIPE)
                assert tar.stdout is not None
                gzip = subprocess.Popen(
                    ["gzip", "--no-name", "--best"],
                    stdin=tar.stdout,
                    stdout=stream,
                )
                tar.stdout.close()
                gzip_status = gzip.wait()
                tar_status = tar.wait()
            if tar_status:
                raise subprocess.CalledProcessError(tar_status, tar_command)
            if gzip_status:
                raise subprocess.CalledProcessError(gzip_status, ["gzip", "--no-name", "--best"])
            partial.replace(output)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    print(f"created {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
