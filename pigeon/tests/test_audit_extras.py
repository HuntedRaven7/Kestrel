"""Tests for audit_sources.py handling of declared extra_sources.

Names declared in the lock's extra_sources are staged at build time by
source_pipeline.py fetch, so the audit must skip them (never report
MISSING, never attempt a dist-git fetch).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import audit_sources as au


def _setup(tmp_path, monkeypatch, spec_body: str, extras: list):
    root = tmp_path
    pkgdir = root / "pigeon" / "packages" / "widg"
    pkgdir.mkdir(parents=True)
    (pkgdir / "widg.spec").write_text(spec_body)
    data = {"packages": {"widg": {
        "version": "3",
        "url_template": "https://example.invalid/widg-{version}.tar.gz",
        "sha512": "0" * 128,
        "filename": "widg-3.tar.gz",
        "extra_sources": extras,
    }}}
    (root / "pigeon" / "config").mkdir(parents=True)
    (root / "pigeon" / "config" / "upstream-sources.json").write_text(
        json.dumps(data))
    monkeypatch.setattr(au, "ROOT", root)
    monkeypatch.setattr(au, "PKGS", root / "pigeon" / "packages")
    return pkgdir


SPEC = "Name: widg\nVersion: 3\nSource0: widg-3.tar.gz\nSource1: side-3.tar.gz\n"


def test_declared_extra_is_skipped(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, monkeypatch, SPEC, [{
        "filename": "side-3.tar.gz",
        "url_template": "https://example.invalid/side-3.tar.gz",
        "sha512": "0" * 128,
    }])
    assert au.audit(fix=True, only="widg") == 0
    assert "STILL MISSING" not in capsys.readouterr().out


def test_undeclared_name_still_missing(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, SPEC, [])
    assert au.audit(fix=False, only="widg") == 1
