"""Tests for packit_source0.py: the create-archive action must print the path
of the factory's already-verified Source0 archive, or a placeholder for
local packages with no upstream source.
"""
import gzip
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rpm-factory" / "tools"))

import packit_source0 as ps0


def _root(tmp_path, entries, specs):
    (tmp_path / "rpm-factory" / "config").mkdir(parents=True)
    (tmp_path / "rpm-factory" / "packages").mkdir(parents=True)
    (tmp_path / "rpm-factory" / "config" / "upstream-sources.json").write_text(
        json.dumps({"packages": entries})
    )
    for s in specs:
        d = tmp_path / "rpm-factory" / "packages" / s
        d.mkdir(parents=True)
        (d / f"{s}.spec").write_text("Name: x\n")
    return tmp_path


def test_verified_source0_returns_staged_archive(tmp_path, monkeypatch):
    _root(tmp_path, {
        "fish": {"version": "4.6.0", "filename": "fish-4.6.0.tar.xz",
                 "sha512": "0" * 128},
    }, ["fish"])
    archive = tmp_path / "rpm-factory" / "packages" / "fish" / "fish-4.6.0.tar.xz"
    archive.write_bytes(b"dummy")
    monkeypatch.setenv("PACKIT_SPECFILE_PATH",
                       str(tmp_path / "rpm-factory" / "packages" / "fish" / "fish.spec"))
    monkeypatch.setenv("PACKAGE", "fish")
    result = ps0.verified_source0(tmp_path)
    assert result == "rpm-factory/packages/fish/fish-4.6.0.tar.xz"


def test_verified_source0_refuses_unstaged_archive(tmp_path, monkeypatch):
    _root(tmp_path, {
        "fish": {"version": "4.6.0", "filename": "fish-4.6.0.tar.xz",
                 "sha512": "0" * 128},
    }, ["fish"])
    monkeypatch.setenv("PACKIT_SPECFILE_PATH",
                       str(tmp_path / "rpm-factory" / "packages" / "fish" / "fish.spec"))
    monkeypatch.setenv("PACKAGE", "fish")
    with pytest.raises(ValueError) as exc:
        ps0.verified_source0(tmp_path)
    assert "not staged" in str(exc.value)


def test_verified_source0_refuses_missing_lock(tmp_path, monkeypatch):
    _root(tmp_path, {}, ["fish"])
    monkeypatch.setenv("PACKIT_SPECFILE_PATH",
                       str(tmp_path / "rpm-factory" / "packages" / "fish" / "fish.spec"))
    monkeypatch.setenv("PACKAGE", "fish")
    with pytest.raises(ValueError) as exc:
        ps0.verified_source0(tmp_path)
    assert "no source lock" in str(exc.value)


def test_placeholder_archive_for_local_packages(tmp_path, monkeypatch):
    _root(tmp_path, {
        "color-filesystem": {"version": "1", "local": True},
    }, ["color-filesystem"])
    monkeypatch.setenv("PACKIT_SPECFILE_PATH",
                       str(tmp_path / "rpm-factory" / "packages" / "color-filesystem"
                           / "color-filesystem.spec"))
    monkeypatch.setenv("PACKAGE", "color-filesystem")
    result = ps0.verified_source0(tmp_path)
    assert result == "color-filesystem-1.tar.gz"
    archive = tmp_path / "rpm-factory" / "packages" / "color-filesystem" / "color-filesystem-1.tar.gz"
    assert archive.is_file()
    # Two runs produce identical bytes (zeroed gzip header).
    first = archive.read_bytes()
    result2 = ps0.verified_source0(tmp_path)
    assert archive.read_bytes() == first
    # The placeholder is an empty gzip: it must decompress to an empty tar.
    with tarfile.open(fileobj=__import__("io").BytesIO(first), mode="r:gz") as tf:
        assert tf.getnames() == []


def test_main_requires_specfile_path(monkeypatch):
    monkeypatch.delenv("PACKIT_SPECFILE_PATH", raising=False)
    with pytest.raises(ValueError):
        ps0.main()