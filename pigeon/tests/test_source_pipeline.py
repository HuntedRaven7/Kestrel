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


def test_local_package_needs_no_fetch(tmp_path, monkeypatch, capsys):
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "filepkg": {"version": "1", "local": True},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.cmd_fetch("filepkg", None) == 0
    assert sp.cmd_record("filepkg", None) == 0


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
    import gzip
    payload = gzip.compress(b"kestrel-test-payload")
    _staged_sources(tmp_path, monkeypatch, payload, hashlib.sha512(payload).hexdigest())
    assert sp.cmd_fetch("fake", None) == 0
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is True


def test_fetch_fails_closed_on_digest_mismatch(tmp_path, monkeypatch, capsys):
    import gzip
    _staged_sources(tmp_path, monkeypatch, gzip.compress(b"real-bytes"), "0" * 128)
    assert sp.cmd_fetch("fake", None) == 1
    assert "verification failed" in capsys.readouterr().out
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is False


def _vendored_setup(tmp_path, monkeypatch, payload: bytes, digest: str | None):
    pkgdir = tmp_path / "pigeon" / "packages" / "gated"
    pkgdir.mkdir(parents=True)
    (pkgdir / "gated-1.tar.gz").write_bytes(payload)
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "gated": {"version": "1",
                  "url_template": "https://example.invalid/gated-{version}.tar.gz",
                  "sha512": digest if digest is not None else "TODO",
                  "vendored": True, "filename": "gated-1.tar.gz"},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sp, "ROOT", tmp_path)


def test_vendored_fetch_verifies_committed_bytes(tmp_path, monkeypatch):
    import gzip
    payload = gzip.compress(b"gated-payload")
    _vendored_setup(tmp_path, monkeypatch, payload, hashlib.sha512(payload).hexdigest())
    assert sp.cmd_fetch("gated", None) == 0


def test_vendored_fetch_fails_on_mismatch(tmp_path, monkeypatch, capsys):
    import gzip
    _vendored_setup(tmp_path, monkeypatch, gzip.compress(b"bytes"), "0" * 128)
    assert sp.cmd_fetch("gated", None) == 1
    assert "verification failed" in capsys.readouterr().out


def test_vendored_record_locks_committed_bytes(tmp_path, monkeypatch):
    import gzip
    payload = gzip.compress(b"gated-payload")
    _vendored_setup(tmp_path, monkeypatch, payload, "TODO")
    # record path needs a digest placeholder that passes the TODO gate:
    # use the vendored record flow directly via cmd_record after staging.
    srcfile = tmp_path / "upstream-sources.json"
    data = json.loads(srcfile.read_text())
    data["packages"]["gated"]["sha512"] = "0" * 128
    srcfile.write_text(json.dumps(data))
    assert sp.cmd_record("gated", None) == 0
    locked = json.loads(srcfile.read_text())["packages"]["gated"]["sha512"]
    assert locked == hashlib.sha512(payload).hexdigest()


def test_check_archive_refuses_html(tmp_path):
    page = tmp_path / "wall.html"
    page.write_text("<!DOCTYPE html><html><body>Sign in</body></html>")
    reason = sp.check_archive(page)
    assert reason is not None and "HTML" in reason


def test_check_archive_accepts_gzip(tmp_path):
    import gzip
    arc = tmp_path / "a.tar.gz"
    arc.write_bytes(gzip.compress(b"data"))
    assert sp.check_archive(arc) is None
