#!/usr/bin/env python3
"""Fetch vendored sources from Fedora Koji or dist-git SRPM.

For packages that can't be downloaded directly (GitLab auth, etc.),
fetch the source RPM from Fedora's Koji and extract sources.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKGS = ROOT / "rpm-factory" / "packages"
ARCHIVE_SUFFIXES = (
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst",
    ".tgz", ".tbz2", ".txz", ".zip", ".crate",
)


def fetch_srpm_from_koji(pkg_name: str, version: str) -> Path | None:
    """Fetch SRPM from Fedora Koji for the given package and version."""
    print(f"  Searching Koji for {pkg_name}-{version}...")

    # Search Koji for the package build
    url = f"https://koji.fedoraproject.org/koji/search?match=glob&type=build&terms={pkg_name}-{version}*"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kestrel-vendored-sources/1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            html = resp.read().decode()
    except Exception as exc:
        print(f"  Failed to search Koji: {exc}")
        return None

    # Parse build IDs from the search results
    build_ids = re.findall(r'buildinfo\?buildID=(\d+)', html)
    if not build_ids:
        print("  No builds found in Koji")
        return None

    # Try each build ID to find the correct version
    for build_id in build_ids[:10]:  # Try first 10 builds
        try:
            url = f"https://koji.fedoraproject.org/koji/buildinfo?buildID={build_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "kestrel-vendored-sources/1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                build_html = resp.read().decode()

            # Check if this is the right version
            if f"{pkg_name}-{version}" not in build_html:
                continue

            # Find SRPM link - look for koji pkg URL pattern
            srpm_match = re.search(r'href="(https://kojipkgs\.fedoraproject\.org//packages/' + re.escape(pkg_name) + r'/\d+\.\d+/\d+\.\w+/src/' + re.escape(pkg_name) + r'-[^"]+\.src\.rpm)"', build_html)
            if not srpm_match:
                # Try more generic pattern
                srpm_match = re.search(r'href="(https://kojipkgs\.fedoraproject\.org//packages/[^"]+\.src\.rpm)"', build_html)
                if not srpm_match:
                    continue

            srpm_url = srpm_match.group(1)
            if not srpm_url.startswith("http"):
                srpm_url = f"https://koji.fedoraproject.org{srpm_url}"

            print(f"  Found SRPM: {srpm_url}")
            return srpm_url

        except Exception as exc:
            print(f"  Error checking build {build_id}: {exc}")
            continue

    return None


def fetch_srpm_from_distgit(pkg_name: str, version: str) -> Path | None:
    """Fetch an SRPM with dnf and return a persistent temporary path."""
    print(f"  Trying dnf download for {pkg_name}-{version}...")

    with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg_name}-") as tmp:
        workdir = Path(tmp)
        try:
            result = subprocess.run(
                ["dnf", "download", "--source", f"{pkg_name}-{version}"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                srpms = list(workdir.glob("*.src.rpm"))
                if srpms:
                    with tempfile.NamedTemporaryFile(
                        prefix="kestrel-srpm-", suffix=".src.rpm", delete=False
                    ) as handle:
                        persistent = Path(handle.name)
                    shutil.copy2(srpms[0], persistent)
                    print(f"  Downloaded SRPM: {persistent.name}")
                    return persistent
        except Exception as exc:
            print(f"  dnf download failed: {exc}")

    return None


def extract_srpm(srpm_path: Path, dest_dir: Path) -> bool:
    """Extract SRPM sources to destination directory."""
    print(f"  Extracting {srpm_path.name} (size: {srpm_path.stat().st_size} bytes)...")
    try:
        # Use rpm2cpio and cpio to extract
        result = subprocess.run(
            ["rpm2cpio", str(srpm_path)],
            capture_output=True,
            timeout=60
        )
        print(f"  rpm2cpio returncode: {result.returncode}")
        if result.returncode != 0:
            print(f"  rpm2cpio failed: stderr={result.stderr.decode()[:200]}")
            return False

        # Extract cpio
        result = subprocess.run(
            ["cpio", "-idmv"],
            input=result.stdout,
            cwd=dest_dir,
            capture_output=True,
            timeout=60
        )
        print(f"  cpio returncode: {result.returncode}")
        if result.returncode != 0:
            print(f"  cpio extraction failed: {result.stderr.decode()[:200]}")
            return False

        return True
    except Exception as exc:
        print(f"  Extraction failed: {exc}")
        return False


def _sha512(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_srpm_archives(extracted: Path, recipe: Path) -> None:
    """Copy only source archives; never let an SRPM replace recipe files."""
    for candidate in extracted.iterdir():
        if candidate.is_file() and candidate.name.endswith(ARCHIVE_SUFFIXES):
            shutil.copy2(candidate, recipe / candidate.name)


def rename_vendor_tarball(pkg_name: str, pkg_dir: Path) -> None:
    """Rename vendor/source tarballs to match spec expectations."""
    # Load package info from upstream-sources.json
    with open(ROOT / "rpm-factory" / "config" / "upstream-sources.json") as f:
        data = json.load(f)
    entry = data["packages"].get(pkg_name, {})
    version = entry.get("version", "")
    upstream_filename = entry.get("filename", "")
    source_filename = entry.get("source_filename", "")
    vendor_filename = entry.get("vendor_filename", "")
    if not version:
        return
    
    # Known tarball renames needed. The pinned SRPM supplies versioned archives;
    # keep the names expected by the spec's %{gosource} expansion.
    renames = {
        "tailscale": {
            "vendor_from_pattern": "tailscale-*-vendored.tar.xz",
            "vendor_to_template": "tailscale-{version}-vendor.tar.xz",
            "source_from_pattern": "v{version}.tar.gz",
            "source_to_template": "v{version}.tar.gz",
        },
        "runc": {
            # Fedora SRPM uses the versioned names expected by %{gosource}.
            "vendor_from_pattern": "runc-*-vendor.tar.bz2",
            "vendor_to_template": "runc-{version}-vendor.tar.bz2",
            "source_from_pattern": "runc-{version}.tar.gz",
            "source_to_template": "runc-{version}.tar.gz",
        },
        "containerd": {
            # Keep the versioned SRPM primary name expected by %{gosource}.
            "source_from_pattern": "containerd-{version}.tar.gz",
            "source_to_template": "containerd-{version}.tar.gz",
        },
        "iio-sensor-proxy": {
            # Upstream source is iio-sensor-proxy-3.9.tar.bz2 (from GitLab)
            # Fedora SRPM provides this directly
            "source_from_pattern": "iio-sensor-proxy-{version}.tar.bz2",
            "source_to_template": "iio-sensor-proxy-{version}.tar.bz2",
        },
    }
    
    if pkg_name not in renames:
        return
    
    rename_info = renames[pkg_name]
    
    # Handle vendor tarball rename
    if "vendor_from_pattern" in rename_info:
        vendor_from_pattern = rename_info["vendor_from_pattern"]
        vendor_to_template = rename_info["vendor_to_template"]
        
        matches = list(pkg_dir.glob(vendor_from_pattern))
        if matches:
            src = matches[0]
            dst_name = vendor_to_template.format(version=version)
            dst = pkg_dir / dst_name
            if src != dst:
                print(f"  Renaming {src.name} -> {dst.name}")
                src.rename(dst)
        # Fallback: if vendor_filename is specified and the target doesn't exist, look for it
        elif vendor_filename:
            vendor_target = vendor_to_template.format(version=version)
            src = pkg_dir / vendor_filename
            dst = pkg_dir / vendor_target
            if src.is_file() and not dst.is_file():
                print(f"  Renaming {src.name} -> {dst.name}")
                src.rename(dst)
    
    # Handle source tarball - ensure Fedora name exists for rpmbuild
    if "source_from_pattern" in rename_info:
        source_from_pattern = rename_info["source_from_pattern"].format(version=version)
        source_to_template = rename_info["source_to_template"]
        
        matches = list(pkg_dir.glob(source_from_pattern))
        if matches:
            src = matches[0]
            dst_name = source_to_template.format(version=version)
            dst = pkg_dir / dst_name
            if src != dst:
                print(f"  Renaming {src.name} -> {dst.name}")
                src.rename(dst)
        
        # Ensure the final name (Fedora name for spec) exists
        final_name = source_to_template.format(version=version)
        final_path = pkg_dir / final_name
        if final_path.is_file():
            print(f"  Source tarball for rpmbuild: {final_name}")
        
        # Also create a copy with upstream filename for source_pipeline verification
        if upstream_filename and upstream_filename != final_name:
            upstream_copy = pkg_dir / upstream_filename
            if not upstream_copy.exists() and final_path.is_file():
                print(f"  Creating copy {final_name} -> {upstream_filename} for verification")
                shutil.copy2(final_path, upstream_copy)


def fetch_vendored_source(pkg_name: str) -> bool:
    """Fetch a digest-pinned vendored SRPM and copy out source archives only."""
    with open(ROOT / "rpm-factory" / "config" / "upstream-sources.json") as stream:
        data = json.load(stream)

    entry = data["packages"].get(pkg_name)
    if not entry:
        print(f"  No upstream-sources entry for {pkg_name}")
        return False
    version = entry.get("version")
    vendor_url = entry.get("vendor_url", "")
    vendor_sha512 = entry.get("vendor_sha512", "")
    if not version or not vendor_url or not vendor_sha512:
        print(f"  REFUSE: {pkg_name} needs version, vendor_url, and vendor_sha512")
        return False

    recipe = PKGS / pkg_name
    if not recipe.is_dir():
        print(f"  Package directory not found: {recipe}")
        return False

    print(f"Fetching vendored sources for {pkg_name} {version}...")
    generated_names = [entry.get("filename", "")]
    generated_names.extend(
        extra.get("filename", "")
        for extra in entry.get("extra_sources", [])
        if extra.get("vendored")
    )
    for name in filter(None, generated_names):
        (recipe / name).unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg_name}-") as temporary:
        temporary_path = Path(temporary)
        srpm_path = temporary_path / f"{pkg_name}.src.rpm"
        extracted = temporary_path / "extracted"
        extracted.mkdir()
        try:
            request = urllib.request.Request(
                vendor_url,
                headers={"User-Agent": "rpm-factory/1"},
            )
            with urllib.request.urlopen(request, timeout=120) as response, srpm_path.open("wb") as output:
                shutil.copyfileobj(response, output)
        except Exception as error:  # noqa: BLE001
            print(f"  Failed to download pinned SRPM: {error}")
            return False

        actual = _sha512(srpm_path)
        if actual != vendor_sha512:
            print(
                "  REFUSE: vendored SRPM SHA-512 mismatch: "
                f"expected {vendor_sha512}, got {actual}"
            )
            return False
        if not extract_srpm(srpm_path, extracted):
            return False
        _copy_srpm_archives(extracted, recipe)
        rename_vendor_tarball(pkg_name, recipe)
        if not ensure_source_tarball(pkg_name, entry, recipe):
            return False
    return True


def ensure_source_tarball(pkg_name: str, entry: dict, pkg_dir: Path) -> bool:
    """Ensure source tarball exists in package directory (download from upstream if needed)."""
    upstream_filename = entry.get("filename", "")
    source_filename = entry.get("source_filename", "")
    url_template = entry.get("url_template", "")
    version = entry.get("version", "")
    
    if not upstream_filename or not url_template or not version:
        return False
    
    # Check if already exists
    upstream_path = pkg_dir / upstream_filename
    if upstream_path.is_file():
        print(f"  Source tarball already present: {upstream_filename}")
        return True
    
    # Try to download from upstream
    url = url_template.replace("{version}", str(version))
    print(f"  Downloading source tarball from upstream: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kestrel-vendored-sources/1"})
        with urllib.request.urlopen(req, timeout=120) as resp, upstream_path.open("wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        print(f"  Downloaded source tarball: {upstream_filename}")
        return True
    except Exception as exc:
        print(f"  Failed to download source tarball from upstream: {exc}")
        return False


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Fetch vendored sources from Fedora Koji/dist-git")
    ap.add_argument("--package", "-p", required=True, help="Package name")
    args = ap.parse_args()

    success = fetch_vendored_source(args.package)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())