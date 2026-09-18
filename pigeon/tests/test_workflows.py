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
