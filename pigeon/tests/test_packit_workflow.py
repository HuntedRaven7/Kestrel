import json
import sys
from pathlib import Path

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


def test_is_local(tmp_path, monkeypatch):
    import importlib.util
    tool = Path(__file__).resolve().parents[2] / "pigeon" / "tools" / "is_local.py"
    spec = importlib.util.spec_from_file_location("is_local", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["kestrel-gdm-config"]) == 0
    assert mod.main(["mango"]) == 1
    assert mod.main([]) == 2
