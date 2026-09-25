# SPDX-FileCopyrightText: Kestrel contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the shared Tine matrix planner."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import matrix


def metadata(names: list[str], chunk_size: int = 2) -> dict:
    return {
        "packages": {name: {} for name in names},
        "chunk_size": chunk_size,
        "chunks": [names[index:index + chunk_size] for index in range(0, len(names), chunk_size)],
    }


def test_plan_uses_generated_chunks() -> None:
    result = matrix.plan(metadata(["a", "b", "c"]))
    assert result["complete"] is True
    assert result["package_count"] == 3
    assert result["matrix"] == [
        {"index": 0, "packages": "a b"},
        {"index": 1, "packages": "c"},
    ]


def test_plan_preserves_metadata_order_for_selection() -> None:
    result = matrix.plan(metadata(["a", "b", "c", "d"], chunk_size=3), "c, a")
    assert result["complete"] is False
    assert result["chunks"] == [["a", "c"]]
    assert result["matrix"] == [{"index": 0, "packages": "a c"}]


def test_plan_rejects_unknown_package() -> None:
    with pytest.raises(ValueError, match="unknown package"):
        matrix.plan(metadata(["a"]), "missing")


def test_plan_rejects_chunks_that_drop_or_duplicate_packages() -> None:
    broken = metadata(["a", "b", "c"])
    broken["chunks"] = [["a"], ["b"]]
    with pytest.raises(ValueError, match="exactly cover"):
        matrix.plan(broken)


def test_write_github_output(tmp_path: Path) -> None:
    output = tmp_path / "github-output"
    matrix._write_github_output(matrix.plan(metadata(["a", "b"])), output)
    assert output.read_text().splitlines() == [
        'matrix=[{"index":0,"packages":"a b"}]',
        "package-count=2",
        "complete=true",
    ]


def test_main_reads_selection_and_writes_output(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "metadata.json"
    source.write_text(json.dumps(metadata(["a", "b", "c"])))
    output = tmp_path / "output"
    monkeypatch.setenv("PACKAGES", "b")
    assert matrix.main(["--metadata", str(source), "--output", str(output)]) == 0
    assert "package-count=1" in output.read_text()
    assert "complete=false" in output.read_text()
    assert "1 chunk(s)" in capsys.readouterr().out
