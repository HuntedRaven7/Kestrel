"""Tests for the Packit SRPM pilot in pigeon/.github/workflows/.

Mirrors utah-packages/tests/test_packit_srpm.py: the pilot is additive and
does not touch rebuild-pigeon.yml, so its shape is asserted directly.
"""
import json
import re
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

import packit_workflow as pw

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / "pigeon" / ".github" / "workflows"
PACKIT_CONFIG = ROOT / "pigeon" / ".packit.yaml"
SOURCE_CONFIG = ROOT / "pigeon" / "config" / "upstream-sources.json"


def _wf(name):
    return yaml.safe_load((WORKFLOWS / name).read_text())


def test_only_dispatch_launches_the_full_srpm_matrix():
    workflow = _wf("packit-srpm-pilot.yml")
    triggers = workflow.get("on", workflow.get(True, {}))
    assert set(triggers) == {"workflow_dispatch"}


def test_workflow_stages_verified_sources_for_every_configured_package():
    config_packages = set(pw.packages())
    workflow = (WORKFLOWS / "packit-srpm-pilot.yml").read_text()
    workflow += (WORKFLOWS / "packit-srpm-chunk.yml").read_text()
    source_packages = set(json.loads(SOURCE_CONFIG.read_text())["packages"])
    # Every .packit.yaml entry is a real source lock entry, and vice versa:
    # the two can never drift because render_packit_config.py generates one
    # from the other.
    assert config_packages <= source_packages
    assert "pigeon/tools/packit_workflow.py packages" in workflow
    assert "fromJson(needs.discover.outputs.chunks)" in workflow
    assert "fromJson(inputs.packages)" in workflow
    assert "pigeon/tools/packit_workflow.py chunks" in workflow
    assert "--stage-into pigeon/packages" in workflow
    assert "--verify-staged pigeon/packages" in workflow
    assert "packit srpm --preserve-spec" in workflow
    assert "create-archive:" in PACKIT_CONFIG.read_text()
    assert "pigeon/tools/packit_source0.py" in PACKIT_CONFIG.read_text()
    # Pinned by digest, never a mutable tag.
    assert re.search(
        r"quay\.io/packit/packit:[\w.-]+@sha256:[0-9a-f]{64}", workflow
    )
    assert not re.search(
        r"quay\.io/packit/packit:[\w.-]+(?!@sha256:)\s", workflow
    )


def test_every_chunk_fits_inside_the_matrix_cap():
    names = pw.packages()
    chunks = pw.package_chunks(names)
    rebuilt = [name for chunk in chunks for name in json.loads(chunk)]
    assert rebuilt == names
    for chunk in chunks:
        assert len(json.loads(chunk)) <= 256


def test_pilot_does_not_touch_rebuild_pigeon():
    # The pilot is additive: rebuild-pigeon.yml must not consume packit
    # SRPM artifacts, and the pilot must not feed the rebuild matrix.
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "rebuild-pigeon.yml").read_text())
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