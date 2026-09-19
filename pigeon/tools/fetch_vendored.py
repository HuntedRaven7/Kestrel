#!/usr/bin/env python3
"""Fetch vendored sources from Fedora Koji or dist-git SRPM.

For packages that can't be downloaded directly (GitLab auth, etc.),
fetch the source RPM from Fedora's Koji and extract sources.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKGS = ROOT / "pigeon" / "packages"


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
    """Fetch SRPM from Fedora dist-git using dnf download."""
    print(f"  Trying dnf download for {pkg_name}-{version}...")

    with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg_name}-") as tmp:
        workdir = Path(tmp)
        try:
            # Try to download SRPM using dnf
            result = subprocess.run(
                ["dnf", "download", "--source", f"{pkg_name}-{version}"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                srpms = list(workdir.glob("*.src.rpm"))
                if srpms:
                    print(f"  Downloaded SRPM: {srpms[0].name}")
                    return srpms[0]
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


def rename_vendor_tarball(pkg_name: str, pkg_dir: Path) -> None:
    """Rename vendor/source tarballs to match spec expectations."""
    # Load package info from upstream-sources.json
    with open(ROOT / "pigeon" / "config" / "upstream-sources.json") as f:
        data = json.load(f)
    entry = data["packages"].get(pkg_name, {})
    version = entry.get("version", "")
    upstream_filename = entry.get("filename", "")
    source_filename = entry.get("source_filename", "")
    vendor_filename = entry.get("vendor_filename", "")
    if not version:
        return
    
    # Known tarball renames needed
    # Fedora SRPM provides source_filename (e.g., runc-1.5.1.tar.gz, containerd-2.3.5.tar.gz)
    # Spec expects the Fedora naming for Source0 (from %{gosource})
    # source_pipeline.py verify-staged looks for upstream_filename (filename field = upstream name)
    # So we need BOTH: keep source_filename for rpmbuild, create copy as upstream_filename for verification
    renames = {
        "tailscale": {
            "vendor_from_pattern": "tailscale-*-vendored.tar.xz",
            "vendor_to_template": "tailscale-{version}-vendor.tar.xz",
            "source_from_pattern": "v{version}.tar.gz",
            "source_to_template": "v{version}.tar.gz",
        },
        "runc": {
            # Fedora SRPM has runc-1.5.1.tar.gz, spec expects runc-1.5.1.tar.gz (from %{gosource})
            # But filename field is v1.5.1.tar.gz for upstream verification
            "vendor_from_pattern": "runc-*-vendor.tar.bz2",
            "vendor_to_template": "runc-{version}-vendor.tar.bz2",
            "source_from_pattern": "runc-{version}.tar.gz",
            "source_to_template": "runc-{version}.tar.gz",  # Keep Fedora name
        },
        "containerd": {
            # Fedora SRPM has containerd-2.3.5.tar.gz, spec expects containerd-2.3.5.tar.gz
            # But filename field is v2.3.5.tar.gz for upstream verification
            "source_from_pattern": "containerd-{version}.tar.gz",
            "source_to_template": "containerd-{version}.tar.gz",  # Keep Fedora name
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
    """Fetch vendored source for a package from Fedora Koji or dist-git."""
    # Load package info from upstream-sources.json
    with open(ROOT / "pigeon" / "config" / "upstream-sources.json") as f:
        data = json.load(f)

    entry = data["packages"].get(pkg_name)
    if not entry:
        print(f"  No upstream-sources entry for {pkg_name}")
        return False

    version = entry.get("version")
    if not version:
        print(f"  No version for {pkg_name}")
        return False

    pkg_dir = PKGS / pkg_name
    if not pkg_dir.is_dir():
        print(f"  Package directory not found: {pkg_dir}")
        return False

    print(f"Fetching vendored sources for {pkg_name} {version}...")

    # Use vendor_url directly if provided (avoids Koji search issues)
    vendor_url = entry.get("vendor_url")
    srpm_url = None
    srpm_path = None

    if vendor_url:
        print(f"  Using vendor_url from upstream-sources.json")
        srpm_url = vendor_url
    else:
        # Try Koji first
        srpm_url = fetch_srpm_from_koji(pkg_name, version)

    if srpm_url:
        with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg_name}-") as tmp:
            srpm_path = Path(tmp) / f"{pkg_name}.src.rpm"
            source_desc = "vendor_url" if vendor_url else "Koji"
            print(f"  Downloading SRPM from {source_desc}...")
            try:
                req = urllib.request.Request(srpm_url, headers={"User-Agent": "kestrel-vendored-sources/1"})
                with urllib.request.urlopen(req, timeout=120) as resp, open(srpm_path, "wb") as f:
                    total = 0
                    while chunk := resp.read(1 << 20):
                        f.write(chunk)
                        total += len(chunk)
                    print(f"  Downloaded {total} bytes")
            except Exception as exc:
                print(f"  Failed to download SRPM from {source_desc}: {exc}")
                srpm_path = None

            # Extract here while temp dir is still alive
            if srpm_path:
                if extract_srpm(srpm_path, PKGS / pkg_name):
                    rename_vendor_tarball(pkg_name, PKGS / pkg_name)
                    # Also ensure source tarball exists (download from upstream if not in SRPM)
                    ensure_source_tarball(pkg_name, entry, PKGS / pkg_name)
                    return True

    # If SRPM download failed, try dnf download from dist-git
    if not srpm_path:
        srpm_path = fetch_srpm_from_distgit(pkg_name, version)
        if srpm_path:
            # Move to temp location for extraction
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp) / srpm_path.name
                srpm_path.rename(tmp_path)
                srpm_path = tmp_path
                if not extract_srpm(srpm_path, PKGS / pkg_name):
                    # Extraction failed, fall through to upstream download
                    srpm_path = None
                else:
                    rename_vendor_tarball(pkg_name, PKGS / pkg_name)
                    ensure_source_tarball(pkg_name, entry, PKGS / pkg_name)
                    return True

    # Last resort: try to download source tarball directly from upstream
    print(f"  Koji/dist-git unavailable, trying upstream download for {pkg_name}...")
    if ensure_source_tarball(pkg_name, entry, PKGS / pkg_name):
        # Also try to get vendor tarball from upstream if possible
        return True

    print(f"  Failed to fetch sources for {pkg_name}")
    return False


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