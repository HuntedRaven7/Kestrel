"""Tests for the Pigeon package inventory (single source of truth).

Mirrors utah-packages/tests/test_package_inventory.py: the inventory is the
enforceable contract, so every reader path is exercised against a tmp repo
rather than the real one.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

import package_inventory as pi


def _root(tmp_path, entries, specs):
    (tmp_path / "pigeon" / "config").mkdir(parents=True)
    (tmp_path / "pigeon" / "packages").mkdir(parents=True)
    (tmp_path / "pigeon" / "config" / "upstream-sources.json").write_text(
        json.dumps({"packages": entries})
    )
    for s in specs:
        d = tmp_path / "pigeon" / "packages" / s
        d.mkdir(parents=True)
        (d / f"{s}.spec").write_text("Name: x\n")
    return tmp_path


def test_inventory_lists_buildable_packages(tmp_path):
    _root(tmp_path, {
        "fish": {"version": "4.6.0", "stage": 4},
        "color-filesystem": {"version": "1", "local": True},
    }, ["fish", "color-filesystem"])
    names = [r.name for r in pi.inventory(tmp_path)]
    assert names == ["color-filesystem", "fish"]


def test_inventory_skips_entries_without_recipe(tmp_path, capsys):
    _root(tmp_path, {"fish": {"version": "4.6.0"}, "todo": {}}, ["fish"])
    assert [r.name for r in pi.inventory(tmp_path)] == ["fish"]
    # inventory() silently skips recipe-less entries; the stderr note lives
    # in packit_workflow.packages(), which is what the matrix consumes.
    assert capsys.readouterr().err == ""


def test_source_locks_rejects_unknown_stage(tmp_path):
    _root(tmp_path, {"fish": {"version": "4.6.0", "stage": 99}}, ["fish"])
    try:
        pi.load_source_locks(tmp_path / "pigeon" / "config" / "upstream-sources.json")
    except ValueError as exc:
        assert "unknown stage" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown stage")


def test_source_locks_defaults_to_stage_2(tmp_path):
    _root(tmp_path, {"fish": {"version": "4.6.0"}}, ["fish"])
    locks = pi.load_source_locks(tmp_path / "pigeon" / "config" / "upstream-sources.json")
    assert locks["fish"]["stage"] == 2


def test_inventory_records_lock_fields(tmp_path):
    _root(tmp_path, {"fish": {"version": "4.6.0", "stage": 4,
                              "filename": "fish-4.6.0.tar.xz"}}, ["fish"])
    rec = pi.inventory(tmp_path)[0]
    assert rec.stage == 4
    assert rec.source_locked is True


def test_inventory_defaults_stage_when_missing_from_lock(tmp_path):
    # A spec dir with no lock entry still builds (stage defaults to 2).
    _root(tmp_path, {"fish": {"version": "4.6.0"}}, ["fish", "unlocked"])
    recs = {r.name: r for r in pi.inventory(tmp_path)}
    assert recs["unlocked"].stage == 2
    assert recs["unlocked"].source_locked is False


def test_render_packit_config_matches_inventory(tmp_path):
    import render_packit_config as rpc
    _root(tmp_path, {
        "fish": {"version": "4.6.0", "stage": 4,
                 "filename": "fish-4.6.0.tar.xz"},
        "color-filesystem": {"version": "1", "local": True},
    }, ["fish", "color-filesystem"])
    out = rpc.render(tmp_path)
    assert "create-archive:" in out
    assert "fish:" in out
    assert "color-filesystem:" in out
    assert "pigeon/packages/fish/fish.spec" in out
    assert "pigeon/packages/color-filesystem/color-filesystem.spec" in out