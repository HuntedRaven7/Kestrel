"""Tests for the Packit SRPM tooling (packit_workflow.py, packit_source0.py).

The packit-srpm pilot workflows were removed, so only the tool-level and
config-level shape is asserted here.
"""
import json
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rpm-factory" / "tools"))

import packit_workflow as pw

ROOT = Path(__file__).resolve().parents[2]
PACKIT_CONFIG = ROOT / "rpm-factory" / ".packit.yaml"


def test_every_chunk_fits_inside_the_matrix_cap():
    names = pw.packages()
    chunks = pw.package_chunks(names)
    rebuilt = [name for chunk in chunks for name in json.loads(chunk)]
    assert rebuilt == names
    for chunk in chunks:
        assert len(json.loads(chunk)) <= 256


def test_pilot_does_not_touch_rebuild_rpm_factory():
    # The pilot is additive: rebuild-rpm-factory.yml must not consume packit
    # SRPM artifacts, and the pilot must not feed the rebuild matrix.
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "rebuild-rpm-factory.yml").read_text())
    text = json.dumps(data)
    assert "packit srpm" not in text
    assert "packit-srpm" not in text
    assert "quay.io/packit/packit" not in text


def test_create_archive_action_stages_verified_source0():
    config = PACKIT_CONFIG.read_text()
    assert "create-archive:" in config
    assert "packit_source0.py" in config
    # The action must be a bash invocation, not a GitHub Action ref.
    assert "bash -c" in config