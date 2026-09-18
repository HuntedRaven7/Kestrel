#!/usr/bin/env python3
"""Audit recipe dirs for spec-referenced files (and optionally fetch them).

Fedora dist-git imports bring the spec + patches but often miss extra
Source1..N files (sysusers units, install scripts, .sig/keys, metainfo)
and lookaside archives. rpmbuild -bs then fails with 'Bad file'.

Usage:
  audit_sources.py                 # report MISSING files, exit 1 if any
  audit_sources.py --fix           # fetch missing dist-git/lookaside files
  audit_sources.py --fix -p foot    # same, scoped to one recipe (for CI matrix)

Rules:
  - The FIRST Source: line per spec is skipped: packit's create_archive
    action overrides Source0 positionally with our verified staged archive.
  - Any reference resolving to our staged archive basename is skipped.
  - Plain filenames must exist in the recipe dir (macros like %{name} are
    expanded from the spec preamble best-effort).
  - Remote (http/ftp) values are warnings only, EXCEPT rpm URL#file
    fragments (e.g. openpgpkey keys), which are fetched into the recipe
    dir so hermetic builds don't need network.
  - *-vendor.tar.bz2 (Go) is reported, not fetched: it must be GENERATED
    with go-vendor-tools (network + Go toolchain), a CI-lane job.
  - --fix downloads from dist-git rawhide (plain files) or the lookaside
    cache (archives + .sig files, via the dist-git `sources` hash file).
"""
from __future__ import annotations

import argparse
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKGS = ROOT / "pigeon" / "packages"
DISTGIT = "https://src.fedoraproject.org/rpms/{pkg}/raw/rawhide/f/{file}"
LOOKASIDE = "https://src.fedoraproject.org/repo/pkgs/{pkg}/{file}/sha512/{hx}/{file}"
ARCHIVE_SUFFIX = (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz", ".zip", ".tar.zst")


def parse_spec(path: Path):
    """Return (macros, first_source_idx, checks) where checks is a list of
    (tag, raw_value) for every Source/Patch line except the first Source."""
    text = path.read_text()
    text = re.sub(r"\\\n", "", text)
    macros = {}
    for m in re.finditer(r"^%(?:global|define)\s+(\w+)\s+(.+?)\s*$", text, re.M):
        macros[m.group(1)] = m.group(2)
    name = version = ""
    m = re.search(r"^Name:\s*(\S+)", text, re.M)
    if m:
        name = m.group(1)
    m = re.search(r"^Version:\s*(\S+)", text, re.M)
    if m:
        version = m.group(1)
    macros.setdefault("name", name)
    macros.setdefault("version", version)
    # rpm defines lowercase %{url} from the URL: tag.
    m = re.search(r"^URL:\s*(\S+)", text, re.M)
    if m:
        macros.setdefault("url", m.group(1))
        macros.setdefault("URL", m.group(1))
    lines = []
    for m in re.finditer(r"^(Source\d*|Patch\d*)\s*:\s*(\S+)", text, re.M):
        lines.append((m.group(1), m.group(2)))
    checks = []
    skipped_first_source = False
    for tag, val in lines:
        if tag.startswith("Source") and not skipped_first_source:
            skipped_first_source = True
            continue
        checks.append((tag, val))
    # %autosetup/%setup -n expectation (only when fully expandable with
    # spec-defined macros; conditional -n values like %{?commitdate:...}
    # for snapshot builds are skipped).
    topdir = None
    m = re.search(r"^%(?:auto)?setup\b[^\n]*-n\s+(\S+)", text, re.M)
    if m:
        expanded = expand(m.group(1), macros)
        if "%{" not in expanded:
            topdir = expanded
    return macros, checks, topdir


def expand(val: str, macros: dict) -> str:
    def sub(m):
        return macros.get(m.group(1), m.group(0))
    prev = None
    while prev != val:
        prev = val
        val = re.sub(r"%\{(\w+)\}", sub, val)
    return val


def fetch(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "kestrel-audit-sources/1"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as f:
            while chunk := resp.read(1024 * 1024):
                f.write(chunk)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"    download failed: {url} ({exc})")
        return False


def distgit_sources(pkg: str) -> dict:
    """Parse the dist-git `sources` hash file: {filename: sha512}."""
    out = {}
    try:
        req = urllib.request.Request(
            DISTGIT.format(pkg=pkg, file="sources"),
            headers={"User-Agent": "kestrel-audit-sources/1"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp.read().decode().splitlines():
                m = re.match(r"SHA512 \((\S+)\) = (\S+)", line)
                if m:
                    out[m.group(1)] = m.group(2)
    except Exception as exc:  # noqa: BLE001
        print(f"    cannot read dist-git sources file for {pkg} ({exc})")
    return out


def try_fetch(pkgdir: Path, stored: str, fetch_name: str, missing: dict) -> None:
    """Attempt dist-git raw, then lookaside-by-basename. Removes `stored`."""
    name = pkgdir.name
    url = DISTGIT.format(pkg=name, file=fetch_name)
    print(f"  fetching {name}/{fetch_name} ...")
    if fetch(url, pkgdir / fetch_name):
        missing[name].remove(stored)
        return
    hashes = distgit_sources(name)
    if fetch_name in hashes:
        lurl = LOOKASIDE.format(pkg=name, file=fetch_name, hx=hashes[fetch_name])
        print(f"  fetching lookaside {name}/{fetch_name} ...")
        if fetch(lurl, pkgdir / fetch_name):
            missing[name].remove(stored)
            return
    print(f"    STILL MISSING: {name}/{stored}")


def staged_names() -> dict:
    """Basename of each entry's rendered URL (what fetch --stage-into stages)."""
    import json

    out = {}
    try:
        data = json.loads((ROOT / "pigeon" / "config" / "upstream-sources.json").read_text())
        for pkg, e in data["packages"].items():
            if e.get("local") or not e.get("url_template"):
                continue
            url = e["url_template"].replace("{version}", str(e.get("version", "")))
            out[pkg] = url.rsplit("/", 1)[-1]
    except Exception:  # noqa: BLE001
        pass
    return out


def audit(fix: bool = False, only: str | None = None) -> int:
    missing, warnings = {}, []
    staged = staged_names()
    dirs = [PKGS / only] if only else sorted(PKGS.iterdir())
    for pkgdir in dirs:
        if not pkgdir.is_dir():
            print(f"no recipe dir: {pkgdir}")
            return 2
        specs = list(pkgdir.glob("*.spec"))
        if not specs:
            continue
        macros, checks, topdir = parse_spec(specs[0])
        for tag, raw in checks:
            val = expand(raw, macros)
            # Our staged verified archive satisfies any reference to it,
            # whatever SourceN position the spec uses (e.g. libinput's
            # snapshot-conditional double Source0).
            if val.rsplit("/", 1)[-1] == staged.get(pkgdir.name):
                continue
            if "vendor.tar" in val:
                if (pkgdir / val.rsplit("/", 1)[-1]).is_file():
                    continue
                warnings.append(
                    f"{pkgdir.name}: {tag} needs go-vendor-tools generation ({raw})"
                )
                continue
            if "://" in val:
                # A committed file satisfying a remote URL (e.g. .sig fetched
                # from lookaside) needs no network; rpmbuild uses the local copy.
                if (pkgdir / val.rsplit("/", 1)[-1]).is_file():
                    continue
                # rpm URL#file fragments (openpgpkey keys): stage the file
                # so rpmbuild finds it without network.
                if "#/" in val:
                    base_url, frag = val.split("#", 1)
                    fname = frag.rsplit("/", 1)[-1]
                    if (pkgdir / fname).is_file():
                        continue
                    missing.setdefault(pkgdir.name, []).append(f"{tag} -> {fname}")
                    if fix:
                        print(f"  fetching {pkgdir.name}/{fname} ...")
                        if fetch(base_url, pkgdir / fname):
                            missing[pkgdir.name].remove(f"{tag} -> {fname}")
                            continue
                        print(f"    STILL MISSING: {pkgdir.name}/{fname}")
                    continue
                warnings.append(f"{pkgdir.name}: {tag} is remote ({val})")
                continue
            if "%{" in val:
                # Unresolvable macro (forge/git0/url, vendor names): try the
                # basename against dist-git raw + lookaside (.sig files live
                # in lookaside); generated trees (vendor tarballs) 404 both.
                base = val.rsplit("/", 1)[-1]
                if (pkgdir / base).is_file():
                    continue
                missing.setdefault(pkgdir.name, []).append(val)
                if fix:
                    try_fetch(pkgdir, val, base, missing)
                continue
            if (pkgdir / val).is_file():
                continue
            missing.setdefault(pkgdir.name, []).append(val)
            if fix:
                try_fetch(pkgdir, val, val, missing)
        # top-dir check against a staged archive, when present
        if topdir:
            for arc in pkgdir.glob("*.tar.*"):
                if arc.name.endswith((".sig", ".asc")):
                    continue
                try:
                    with tarfile.open(arc) as tf:
                        first = tf.getnames()[0].split("/")[0]
                    if first != topdir:
                        warnings.append(
                            f"{pkgdir.name}: {arc.name} extracts to {first!r}, "
                            f"spec expects {topdir!r}"
                        )
                except Exception:  # noqa: BLE001
                    pass
    for w in sorted(warnings):
        print(f"WARN: {w}")
    still = {k: v for k, v in missing.items() if v}
    if still:
        print("MISSING:")
        for k in sorted(still):
            for f in still[k]:
                print(f"  {k}: {f}")
        return 1
    print(f"source audit OK ({sum(1 for _ in PKGS.iterdir() if _.is_dir())} recipe dirs)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit (and fetch) spec-referenced files")
    ap.add_argument("--fix", action="store_true", help="fetch missing files into recipe dirs")
    ap.add_argument("--package", "-p", default=None, help="scope to one recipe dir (for CI matrix)")
    args = ap.parse_args(argv)
    return audit(fix=args.fix, only=args.package)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
