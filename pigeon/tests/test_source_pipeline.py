import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

import source_pipeline as sp


def test_fetch_refuses_unknown_package(capsys):
    assert sp.cmd_fetch("no-such-pkg", None) == 1
    assert "no upstream-sources.json entry" in capsys.readouterr().out


def test_fetch_refuses_unversioned_package(tmp_path, monkeypatch, capsys):
    # A source entry with no agreed version/URL must refuse without network.
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "future": {"version": "TODO", "url_template": "TODO-x", "sha512": "TODO"},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.cmd_fetch("future", None) == 1
    assert "not fetchable" in capsys.readouterr().out
    assert sp.cmd_record("future", None) == 1


def test_local_package_needs_no_fetch(capsys):
    assert sp.cmd_fetch("kestrel-gdm-config", None) == 0
    assert sp.cmd_record("kestrel-gdm-config", None) == 0


def test_entry_ready_gate():
    assert sp.entry_ready({"local": True}) is None
    assert sp.entry_ready({"version": "TODO"}) is not None
    assert sp.entry_ready({"version": "1", "url_template": "TODO-x"}) is not None
    assert sp.entry_ready({"version": "1", "url_template": "https://x/{version}.tar.gz"}) is None


def test_signature_dormant_without_config(tmp_path):
    result = sp.verify_signature({}, tmp_path / "a.tar.gz", tmp_path)
    assert result == {"checked": False, "reason": "no signature configured"}


def _staged_sources(tmp_path, monkeypatch, payload: bytes, sha512: str):
    archive = tmp_path / "fake-1.tar.gz"
    archive.write_bytes(payload)
    sources = {
        "packages": {
            "fake": {
                "version": "1",
                # file:// URL with {version} placeholder pointing at the staged archive.
                "url_template": f"file://{tmp_path}/fake-{{version}}.tar.gz",
                "sha512": sha512,
            }
        }
    }
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps(sources))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")


def test_fetch_verifies_staged_archive(tmp_path, monkeypatch):
    payload = b"kestrel-test-payload"
    _staged_sources(tmp_path, monkeypatch, payload, hashlib.sha512(payload).hexdigest())
    assert sp.cmd_fetch("fake", None) == 0
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is True


def test_fetch_fails_closed_on_digest_mismatch(tmp_path, monkeypatch, capsys):
    _staged_sources(tmp_path, monkeypatch, b"real-bytes", "0" * 128)
    assert sp.cmd_fetch("fake", None) == 1
    assert "verification failed" in capsys.readouterr().out
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is False
