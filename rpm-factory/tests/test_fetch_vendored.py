"""Security contract for digest-pinned vendored SRPM extraction."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rpm-factory" / "tools"))

import fetch_vendored as fv


def test_srpm_extraction_copies_only_archives(tmp_path):
    extracted = tmp_path / "extracted"
    recipe = tmp_path / "recipe"
    extracted.mkdir()
    recipe.mkdir()
    (extracted / "source.tar.zst").write_bytes(b"source")
    (extracted / "vendor.tar.bz2").write_bytes(b"vendor")
    (extracted / "package.spec").write_text("Name: package\n")
    (extracted / "go-vendor-tools.toml").write_text("untrusted = true\n")

    fv._copy_srpm_archives(extracted, recipe)

    assert (recipe / "source.tar.zst").read_bytes() == b"source"
    assert (recipe / "vendor.tar.bz2").read_bytes() == b"vendor"
    assert not (recipe / "package.spec").exists()
    assert not (recipe / "go-vendor-tools.toml").exists()


def test_vendored_entry_without_digest_pin_is_refused(tmp_path, monkeypatch, capsys):
    config = tmp_path / "rpm-factory" / "config"
    packages = tmp_path / "rpm-factory" / "packages" / "demo"
    config.mkdir(parents=True)
    packages.mkdir(parents=True)
    (config / "upstream-sources.json").write_text(json.dumps({"packages": {
        "demo": {"version": "1", "vendored": True}
    }}))
    monkeypatch.setattr(fv, "ROOT", tmp_path)
    monkeypatch.setattr(fv, "PKGS", tmp_path / "rpm-factory" / "packages")

    assert not fv.fetch_vendored_source("demo")
    assert "needs version, vendor_url, and vendor_sha512" in capsys.readouterr().out


def test_vendored_srpm_digest_mismatch_is_refused_before_extraction(
    tmp_path, monkeypatch, capsys
):
    config = tmp_path / "rpm-factory" / "config"
    packages = tmp_path / "rpm-factory" / "packages" / "demo"
    config.mkdir(parents=True)
    packages.mkdir(parents=True)
    srpm = tmp_path / "demo.src.rpm"
    srpm.write_bytes(b"pinned SRPM bytes")
    (config / "upstream-sources.json").write_text(json.dumps({"packages": {
        "demo": {
            "version": "1",
            "vendored": True,
            "vendor_url": srpm.as_uri(),
            "vendor_sha512": "0" * 128,
        }
    }}))
    monkeypatch.setattr(fv, "ROOT", tmp_path)
    monkeypatch.setattr(fv, "PKGS", tmp_path / "rpm-factory" / "packages")
    monkeypatch.setattr(
        fv,
        "extract_srpm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not extract")),
    )

    assert not fv.fetch_vendored_source("demo")
    assert "SRPM SHA-512 mismatch" in capsys.readouterr().out


def test_configured_vendored_srpm_hashes_are_current():
    registry = json.loads(
        (ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text()
    )["packages"]
    for package in ("containerd", "runc"):
        entry = registry[package]
        assert entry["vendor_url"].startswith("https://")
        assert len(entry["vendor_sha512"]) == 128
        assert len(entry["extra_sources"]) == 1
        assert entry["extra_sources"][0]["vendored"] is True
        assert len(entry["extra_sources"][0]["sha512"]) == 128
