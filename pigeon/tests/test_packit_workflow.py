import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

import packit_workflow as pw


def _root(tmp_path, monkeypatch, entries, specs):
    (tmp_path / "pigeon" / "config").mkdir(parents=True)
    (tmp_path / "pigeon" / "packages").mkdir(parents=True)
    (tmp_path / "pigeon" / "config" / "upstream-sources.json").write_text(
        json.dumps({"packages": {e: {} for e in entries}})
    )
    for s in specs:
        d = tmp_path / "pigeon" / "packages" / s
        d.mkdir(parents=True)
        (d / f"{s}.spec").write_text("Name: x\n")
    monkeypatch.setattr(pw, "ROOT", tmp_path)
    return tmp_path


def test_packages_skips_entries_without_recipe(tmp_path, monkeypatch, capsys):
    _root(tmp_path, monkeypatch, ["built", "todo"], ["built"])
    assert pw.packages() == ["built"]
    assert "todo" in capsys.readouterr().err


def test_packages_empty_without_recipes(tmp_path, monkeypatch):
    _root(tmp_path, monkeypatch, ["todo"], [])
    assert pw.packages() == []


def test_chunks_split_large_lists():
    names = [f"pkg-{i}" for i in range(500)]
    chunks = pw.package_chunks(names, size=250)
    assert len(chunks) == 2
    for chunk in chunks:
        assert len(json.loads(chunk)) <= 250
    # No package is dropped or duplicated across chunks.
    flat = [n for chunk in chunks for n in json.loads(chunk)]
    assert sorted(flat) == sorted(names)


def test_chunks_rejects_bad_size():
    with pytest.raises(ValueError):
        pw.package_chunks(["a"], size=0)


def test_main_packages_and_chunks(tmp_path, monkeypatch):
    _root(tmp_path, monkeypatch, ["built", "todo"], ["built"])
    assert pw.main(["packages"]) == 0
    assert pw.main(["chunks"]) == 0