"""Embedded shell in workflows must parse: a stray apostrophe inside
`bash -exc '...'` terminates the quoting and fails the whole step
(see: "syntax error near unexpected token `('")."""
import subprocess
import tempfile
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _inner_scripts():
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        data = yaml.safe_load(wf.read_text())
        for job in (data.get("jobs") or {}).values():
            for step in job.get("steps", []) or []:
                run = step.get("run", "")
                if "bash -exc '" not in run:
                    continue
                inner = run.split("bash -exc '", 1)[1].rsplit("'", 1)[0]
                yield f"{wf.name}:{step.get('name')}", inner


def test_embedded_bash_parses():
    scripts = list(_inner_scripts())
    assert scripts, "no embedded bash blocks found"
    for label, inner in scripts:
        # No unbalanced single quotes: only the two delimiters may exist,
        # and they were split off above, so none may remain.
        assert "'" not in inner, f"{label}: stray apostrophe breaks quoting"
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
            f.write(inner.replace("$PACKAGE", "testpkg"))
        try:
            proc = subprocess.run(["bash", "-n", f.name],
                                  capture_output=True, text=True, timeout=60)
        finally:
            Path(f.name).unlink()
        assert proc.returncode == 0, f"{label}: {proc.stderr.strip()[:300]}"


def _rebuild_pigeon():
    return yaml.safe_load((WORKFLOWS / "rebuild-pigeon.yml").read_text())


def _build_stages(data):
    """Stage numbers dispatched to build-stage.yml, e.g. {'0',...}."""
    stages = set()
    for job in data["jobs"].values():
        if not isinstance(job, dict) or "build-stage" not in str(job.get("uses", "")):
            continue
        stages.add(str(job["with"]["stage"]).strip('"'))
    return stages


def test_precedence_waits_for_all_stages():
    # Every rebuildN wave must finish before the precedence gate downloads
    # stage-* artifacts; otherwise publish runs on an incomplete set.
    data = _rebuild_pigeon()
    rebuilds = sorted(j for j in data["jobs"] if j.startswith("rebuild"))
    assert rebuilds, "no rebuild jobs found"
    needs = data["jobs"]["precedence"]["needs"]
    for job in rebuilds:
        assert job in needs, (
            f"precedence does not wait for {job}: "
            f"its artifacts may miss the publish")


def test_publish_collects_all_stages():
    # The repository assembly loop must copy every built stage dir,
    # or built RPMs never reach the GHCR image.
    data = _rebuild_pigeon()
    stages = _build_stages(data)
    assert stages, "no build-stage dispatches found"
    publish = data["jobs"]["publish"]
    runs = [s.get("run", "") for s in publish.get("steps", []) or []]
    assembly = next(r for r in runs if "stage-$stage" in r)
    for stage in sorted(stages):
        assert stage in assembly, (
            f"publish assembly drops stage {stage}: "
            f"built RPMs never reach GHCR")
