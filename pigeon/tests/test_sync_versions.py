"""Tests for sync_versions.py (lock is the single source of truth)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import sync_versions as sv


def _root(tmp_path, specs: dict, lock: dict):
    pkgs = tmp_path / "pkgs"
    pkgs.mkdir()
    for name, spec_ver in specs.items():
        d = pkgs / name
        d.mkdir()
        (d / f"{name}.spec").write_text(f"Name: {name}\nVersion:        {spec_ver}\n")
    return pkgs, {"packages": lock}


def test_no_drift_when_in_sync(tmp_path):
    pkgs, data = _root(tmp_path, {"a": "1.0"},
                       {"a": {"version": "1.0"}})
    assert sv.drift_for(pkgs, data) == []


def test_drift_detected(tmp_path):
    pkgs, data = _root(tmp_path, {"a": "1.0"},
                       {"a": {"version": "2.0"}})
    assert sv.drift_for(pkgs, data) == [("a", "1.0", "2.0")]


def test_macroized_version_skipped(tmp_path):
    pkgs, data = _root(tmp_path, {"a": "%{major}.0"},
                       {"a": {"version": "1.0"}})
    assert sv.drift_for(pkgs, data) == []


def test_local_entries_and_missing_specs_skipped(tmp_path):
    pkgs = tmp_path / "pkgs"
    pkgs.mkdir()
    (pkgs / "nospec").mkdir()
    data = {"packages": {
        "nospec": {"version": "1.0"},
        "filepkg": {"version": "1", "local": True},
    }}
    assert sv.drift_for(pkgs, data) == []


def test_sync_rewrites_only_the_version(tmp_path):
    pkgs, data = _root(tmp_path, {"a": "1.0"},
                       {"a": {"version": "2.0"}})
    assert sv.sync_package(pkgs / "a", "2.0") is True
    text = (pkgs / "a" / "a.spec").read_text()
    assert "Version:        2.0\n" in text
    assert "Name: a\n" in text
    assert sv.sync_package(pkgs / "a", "2.0") is False


def test_main_check_and_sync(tmp_path, monkeypatch, capsys):
    pkgs, data = _root(tmp_path, {"a": "1.0"},
                       {"a": {"version": "2.0"}})
    monkeypatch.setattr(sv, "PKGS", pkgs)
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps(data))
    monkeypatch.setattr(sv, "SOURCES", srcfile)
    assert sv.main(["--check"]) == 1
    assert "version drift for a" in capsys.readouterr().out
    assert sv.main([]) == 0
    assert (pkgs / "a" / "a.spec").read_text().count("2.0") == 1
    assert sv.main(["--check"]) == 0
