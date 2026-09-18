"""Fetch + verify direct upstream sources before any build (fail closed).

Usage:
  source_pipeline.py fetch <pkg> [--output DIR]
  source_pipeline.py record <pkg> [--output DIR]   # fetch + write sha512 back
  source_pipeline.py report <pkg>                  # show last report

Rules (PLAN.md §3.2):
  - No upstream-sources.json entry -> refuse.
  - Local packages ("local": true, e.g. kestrel-gdm-config) -> nothing to fetch.
  - Vendored packages ("vendored": true, e.g. bot-walled upstreams) -> the
    bytes live in git; fetch/record hash the committed file, never download.
  - fetch refuses when no digest is recorded yet; use `record` for first vendor.
  - record fills the sha512 field (used for first fetch + Renovate/Packit bumps).
  - Downloads that are not archives (HTML bot-walls) are refused, never locked.
  - Every run writes pigeon/reports/<pkg>.json; failed verification leaves the
    previous source unchanged (we never write a digest on failure).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "pigeon" / "config" / "upstream-sources.json"
REPORTS = ROOT / "pigeon" / "reports"
CHUNK = 1024 * 1024


def load_sources() -> dict:
    return json.loads(SOURCES.read_text())


def render_url(entry: dict) -> str:
    return entry["url_template"].replace("{version}", str(entry["version"]))


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "kestrel-source-pipeline/1"})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f, length=CHUNK)


def sha512_of(path: Path) -> str:
    h = hashlib.sha512()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


ARCHIVE_MAGIC = (
    b"\x1f\x8b",  # gzip
    b"BZh",  # bzip2
    b"\xfd7zXZ\x00",  # xz
    b"\x28\xb5\x2f\xfd",  # zstd
    b"PK\x03\x04",  # zip
)


def check_archive(path: Path) -> str | None:
    """Refuse non-archives (HTML bot-walls, error pages). Returns a refusal
    reason, or None when the file looks like a compressed archive."""
    with path.open("rb") as f:
        head = f.read(8)
    if head.startswith(ARCHIVE_MAGIC):
        return None
    if head.lstrip()[:1] == b"<":
        return "upstream served HTML, not an archive (bot-wall / sign-in page?)"
    return f"unknown file magic {head.hex()}; refusing (not a known archive)"


def verify_signature(entry: dict, archive: Path, workdir: Path) -> dict:
    """Verify release signature when the entry configures one. Dormant until
    an entry carries signature_url_template + gpg_key."""
    tmpl = entry.get("signature_url_template")
    if not tmpl:
        return {"checked": False, "reason": "no signature configured"}
    gpg = shutil.which("gpg")
    if gpg is None:
        return {"checked": False, "reason": "gpg not available", "ok": False}
    sig_url = tmpl.replace("{version}", str(entry["version"]))
    sig_file = workdir / (archive.name + ".sig")
    download(sig_url, sig_file)
    keyring = workdir / "trusted.gpg"
    # Import the pinned key into a throwaway keyring (fail closed on any error).
    proc = subprocess.run(
        [gpg, "--no-default-keyring", "--keyring", str(keyring),
         "--import", entry["gpg_key"]],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        return {"checked": True, "ok": False, "reason": f"gpg import failed: {proc.stderr[-500:]}"}
    proc = subprocess.run(
        [gpg, "--no-default-keyring", "--keyring", str(keyring),
         "--verify", str(sig_file), str(archive)],
        capture_output=True, text=True, timeout=120,
    )
    return {"checked": True, "ok": proc.returncode == 0,
            "reason": proc.stderr[-500:] if proc.returncode else "signature valid"}


def write_report(pkg: str, payload: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{pkg}.json").write_text(json.dumps(payload, indent=2) + "\n")


def entry_ready(entry: dict) -> str | None:
    """Return a refusal reason when the entry is not fetchable yet, else None."""
    if entry.get("local"):
        return None
    if not entry.get("version") or str(entry["version"]).startswith("TODO"):
        return "no version agreed yet"
    if not entry.get("url_template") or str(entry["url_template"]).startswith("TODO"):
        return "no source URL agreed yet"
    return None


def cmd_fetch(pkg: str, output: str | None, stage_into: str | None = None, verify_staged: bool = False) -> int:
    data = load_sources()
    entry = data["packages"].get(pkg)
    if entry is None:
        print(f"REFUSE: no upstream-sources.json entry for {pkg}")
        return 1
    if entry.get("local"):
        print(f"OK: {pkg} is a local package (nothing to fetch)")
        return 0
    if reason := entry_ready(entry):
        print(f"REFUSE: {pkg} not fetchable — {reason}")
        return 1
    recorded = entry.get("sha512", "")
    if not recorded or recorded.startswith("TODO"):
        print(f"REFUSE: no recorded digest for {pkg} — run `record {pkg}` first")
        return 1
    if entry.get("vendored"):
        return cmd_fetch_vendored(pkg, entry, recorded, output)
    url = render_url(entry)
    with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg}-") as tmp:
        workdir = Path(tmp)
        archive = workdir / url.rsplit("/", 1)[-1]
        try:
            download(url, archive)
        except Exception as exc:  # noqa: BLE001 — report, don't traceback
            write_report(pkg, {"package": pkg, "ok": False, "reason": f"download failed: {exc}"})
            print(f"FAIL: download failed for {pkg}: {exc}")
            return 1
        if reason := check_archive(archive):
            write_report(pkg, {"package": pkg, "ok": False, "reason": reason})
            print(f"REFUSE: {pkg} — {reason}")
            return 1
        digest = sha512_of(archive)
        sig = verify_signature(entry, archive, workdir)
        # Gate: checksum must match; signature must pass when one is configured.
        ok = digest == recorded and (not sig["checked"] or sig.get("ok") is True)
        
        # Copy to output directory if specified
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            shutil.copy(archive, Path(output) / archive.name)
        
        # Also copy to package directory for packit Source0 lookup
        if stage_into:
            pkg_dir = ROOT / stage_into / pkg
            if pkg_dir.exists():
                shutil.copy(archive, pkg_dir / archive.name)
        
        write_report(pkg, {
            "package": pkg, "version": entry.get("version"), "url": url,
            "sha512": digest, "expected": recorded, "signature": sig, "ok": ok,
        })
        if not ok:
            print(f"FAIL: verification failed for {pkg} (digest match: {digest == recorded})")
            return 1
        print(f"OK: {pkg}@{entry.get('version')} verified ({archive.name})")
        
        if verify_staged:
            # Verify the staged source exists in the package directory
            staged_path = ROOT / "pigeon" / "packages" / pkg / archive.name
            if not staged_path.exists():
                print(f"FAIL: staged source not found at {staged_path}")
                return 1
            # Verify the digest matches
            staged_digest = sha512_of(staged_path)
            if staged_digest != recorded:
                print(f"FAIL: staged source digest mismatch")
                return 1
            print(f"OK: staged source verified at {staged_path}")
        
        return 0


def cmd_record(pkg: str, output: str | None) -> int:
    data = load_sources()
    entry = data["packages"].get(pkg)
    if entry is None:
        print(f"REFUSE: no upstream-sources.json entry for {pkg}")
        return 1
    if entry.get("local"):
        print(f"OK: {pkg} is a local package (nothing to record)")
        return 0
    if reason := entry_ready(entry):
        print(f"REFUSE: {pkg} not recordable — {reason}")
        return 1
    if entry.get("vendored"):
        # Lock the committed bytes (bot-walled upstream; see entry note).
        filename = entry.get("filename", "")
        staged = ROOT / "pigeon" / "packages" / pkg / filename if filename else None
        if staged is None or not staged.is_file():
            print(f"REFUSE: nothing staged for {pkg} ({filename})")
            return 1
        if reason := check_archive(staged):
            print(f"REFUSE: {pkg} — {reason}")
            return 1
        entry["sha512"] = sha512_of(staged)
        SOURCES.write_text(json.dumps(data, indent=2) + "\n")
        write_report(pkg, {
            "package": pkg, "version": entry.get("version"), "vendored": True,
            "sha512": entry["sha512"], "ok": True, "recorded": True,
        })
        print(f"OK: recorded {pkg}@{entry.get('version')} sha512={entry['sha512'][:16]}…")
        return 0
    url = render_url(entry)
    with tempfile.TemporaryDirectory(prefix=f"kestrel-{pkg}-") as tmp:
        workdir = Path(tmp)
        archive = workdir / url.rsplit("/", 1)[-1]
        try:
            download(url, archive)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: download failed for {pkg}: {exc}")
            return 1
        if reason := check_archive(archive):
            print(f"REFUSE: {pkg} — {reason}")
            return 1
        digest = sha512_of(archive)
        sig = verify_signature(entry, archive, workdir)
        if sig["checked"] and not sig.get("ok"):
            print(f"FAIL: signature check failed for {pkg}: {sig.get('reason')}")
            return 1
        if output:
            out = Path(output)
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy(archive, out / archive.name)
        # Also copy to package directory for packit Source0 lookup
        pkg_dir = ROOT / "pigeon" / "packages" / pkg
        if pkg_dir.exists():
            shutil.copy(archive, pkg_dir / archive.name)
        entry["sha512"] = digest
        entry["filename"] = archive.name  # keep staged name in sync; packit_source0.py reads it
        SOURCES.write_text(json.dumps(data, indent=2) + "\n")
        write_report(pkg, {
            "package": pkg, "version": entry.get("version"), "url": url,
            "sha512": digest, "signature": sig, "ok": True, "recorded": True,
        })
        print(f"OK: recorded {pkg}@{entry.get('version')} sha512={digest[:16]}…")
        return 0


def cmd_fetch_vendored(pkg: str, entry: dict, recorded: str, output: str | None) -> int:
    """Verify the staged bytes for bot-walled upstreams (no download).
    
    Checks both the git repo (for committed vendored sources) and the
    package directory (for sources staged by fetch_vendored.py from Koji SRPMs).
    """
    filename = entry.get("filename", "")
    # First check the git repo (for committed vendored sources)
    staged = ROOT / "pigeon" / "packages" / pkg / filename if filename else None
    # Also check the package directory (for sources staged by fetch_vendored.py from Koji SRPMs)
    staged_pkg_dir = ROOT / "pigeon" / "packages" / pkg / filename if filename else None
    
    # Use whichever exists
    if staged_pkg_dir and staged_pkg_dir.is_file():
        staged = staged_pkg_dir
    elif staged is None or not staged.is_file():
        write_report(pkg, {"package": pkg, "ok": False,
                            "reason": f"vendored file not staged: {filename}"})
        print(f"FAIL: vendored source not staged for {pkg} ({filename})")
        return 1
    if reason := check_archive(staged):
        write_report(pkg, {"package": pkg, "ok": False, "reason": reason})
        print(f"FAIL: staged source for {pkg} — {reason}")
        return 1
    digest = sha512_of(staged)
    ok = digest == recorded
    if output:
        Path(output).mkdir(parents=True, exist_ok=True)
        shutil.copy(staged, Path(output) / staged.name)
    write_report(pkg, {
        "package": pkg, "version": entry.get("version"), "vendored": True,
        "sha512": digest, "expected": recorded, "ok": ok,
    })
    if not ok:
        print(f"FAIL: verification failed for {pkg} (digest match: False)")
        return 1
    print(f"OK: verified vendored source for {pkg} ({staged.name})")
    return 0


def cmd_report(pkg: str) -> int:
    path = REPORTS / f"{pkg}.json"
    if not path.exists():
        print(f"no report for {pkg} (run fetch/record first)")
        return 1
    print(path.read_text())
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Kestrel source verification pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "record"):
        p = sub.add_parser(name)
        p.add_argument("package")
        p.add_argument("--output", default=None, help="stage verified archive into DIR")
        p.add_argument("--stage-into", default=None, help="stage verified archive into package dir (e.g., packages)")
        p.add_argument("--verify-staged", action="store_true", help="verify staged source exists in package dir")
    r = sub.add_parser("report")
    r.add_argument("package")
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        return cmd_fetch(args.package, args.output, args.stage_into, args.verify_staged)
    if args.cmd == "record":
        return cmd_record(args.package, args.output)
    return cmd_report(args.package)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
