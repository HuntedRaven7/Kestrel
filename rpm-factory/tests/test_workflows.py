"""Workflow and generated Tine graph contracts."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTION = ROOT / ".github" / "actions" / "tine-build" / "action.yml"


def _workflow(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text())


def test_workflow_yaml_parses() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        assert isinstance(data, dict), path
        assert data.get("jobs"), path


def test_embedded_bash_parses() -> None:
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        data = yaml.safe_load(workflow.read_text())
        for job in (data.get("jobs") or {}).values():
            for step in job.get("steps", []) or []:
                script = step.get("run", "")
                if "bash -exc '" not in script:
                    continue
                inner = script.split("bash -exc '", 1)[1].rsplit("'", 1)[0]
                assert "'" not in inner, f"{workflow.name}:{step.get('name')}"
                with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
                    handle.write(inner)
                try:
                    result = subprocess.run(["bash", "-n", handle.name], capture_output=True, text=True)
                finally:
                    Path(handle.name).unlink()
                assert result.returncode == 0, result.stderr


def test_rebuild_uses_tine_chunks_and_promotes_only_complete_verified_builds() -> None:
    data = _workflow("rebuild-rpm-factory.yml")
    jobs = data["jobs"]
    assert {"prepare", "build", "publish", "trivy-scan", "promote"} <= set(jobs)
    workflow_text = (WORKFLOWS / "rebuild-rpm-factory.yml").read_text()
    assert "build-stage.yml" not in workflow_text
    build = jobs["build"]
    assert build["needs"] == "prepare"
    assert "include" in build["strategy"]["matrix"]
    step = next(step for step in build["steps"] if step.get("uses") == "./.github/actions/tine-build")
    assert step["with"]["expected-tine-sha"] == "4c80c7bd771233002b36ec80568d3a252a468aa2"
    assert "${{ matrix.packages }}" == step["with"]["packages"]
    assert "needs.prepare.outputs.complete == 'true'" in jobs["publish"]["if"]
    assert jobs["publish"]["needs"] == ["prepare", "build"]
    assert jobs["promote"]["needs"] == ["publish", "trivy-scan"]
    assert "rpm-factory-chunk-*" in workflow_text
    assert "candidate-${{ github.run_id }}-${{ github.run_attempt }}" in workflow_text
    assert "scan-type: sbom" in workflow_text
    assert "limit-severities-for-sarif: true" in workflow_text
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in workflow_text
    assert "cosign sign --yes" in workflow_text


def test_tine_action_is_pinned_and_cache_safe() -> None:
    data = yaml.safe_load(ACTION.read_text())
    assert data["runs"]["using"] == "composite"
    text = ACTION.read_text()
    workflow_text = (ROOT / ".github" / "workflows" / "rebuild-rpm-factory.yml").read_text()
    assert "4c80c7bd771233002b36ec80568d3a252a468aa2" in workflow_text
    assert "EXPECTED_TINE_SHA" in text
    assert "tine init" not in text
    assert "buck-out" not in text
    assert "actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in text
    assert "actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in text
    assert "tine/buck2" in text
    assert "sha256" in text
    assert 'kestrel-rpm-factory-tine-v2-${PLATFORM}' in text
    assert "rpm-factory/tools/*.py" in text
    assert "ARTIFACT-MANIFEST.sha256" in text
    assert "sha256sum --check --strict" in text


def test_image_builds_require_a_full_rpm_factory_digest() -> None:
    expected_steps = {
        "build-warbler.yml": "Build Warbler image",
        "build-woodpecker.yml": "Build Woodpecker image",
    }
    for name, step_name in expected_steps.items():
        data = _workflow(name)
        trigger = data.get("on", data.get(True))
        digest_input = trigger["workflow_dispatch"]["inputs"]["rpm_factory_image_sha"]
        assert digest_input["required"] is True
        build = next(
            step
            for job in data["jobs"].values()
            for step in job.get("steps", [])
            if step.get("name") == step_name
        )
        assert build["env"]["RPM_FACTORY_IMAGE_SHA"] == "${{ inputs.rpm_factory_image_sha }}"
        assert "^sha256:[a-f0-9]{64}$" in build["run"]
        verify = next(
            step
            for job in data["jobs"].values()
            for step in job.get("steps", [])
            if step.get("name") == "Verify rpm-factory image signature"
        )
        assert "cosign verify" in verify["run"]
        assert "rebuild-rpm-factory.yml@refs/heads/main" in verify["run"]


def test_generated_tine_projection_matches_package_lock() -> None:
    metadata = json.loads((ROOT / "rpm-factory" / "config" / "tine-packages.json").read_text())
    lock = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())["packages"]
    assert len(metadata["packages"]) == 145
    assert set(metadata["packages"]) <= set(lock)
    assert metadata["dist"] == ".hum1.rpmfactory"
    buck = (ROOT / "rpm-factory" / "BUCK").read_text()
    assert 'name = "brightnessctl"' in buck
    assert 'name = "wlroots"' in buck
    assert "filegroup(" not in buck
    assert '".tine-sources/adwaita-fonts/*"' in buck
    assert '"packages/adwaita-fonts/*"' not in buck
