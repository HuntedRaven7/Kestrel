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


def _build_stage():
    return yaml.safe_load((WORKFLOWS / "build-stage.yml").read_text())


def test_package_cache_restores_before_compiling_and_publishes_misses():
    # Per-package GHCR cache: resolve key -> restore attempt -> compile
    # only on miss -> publish the miss. A hit must be indistinguishable
    # from a build downstream (same stage artifact either way).
    data = _build_stage()
    steps = data["jobs"]["build"]["steps"]
    names = [s.get("name", "") for s in steps]
    assert "Resolve build root for cache key" in names
    assert "Restore package RPM cache" in names
    assert "Publish package RPM cache" in names
    assert "tools/package_cache_key.py" in yaml.safe_dump(data)
    by_name = {s.get("name", ""): s for s in steps}
    build = by_name["Build in Fedora container"]
    assert "package_cache_restore" in build.get("if", ""), (
        "the compile must be skipped on a cache hit")
    assert "hit != 'true'" in build.get("if", "")


def test_cache_hit_materialises_as_the_ordinary_stage_artifact():
    # Precedence/publish only ever see ~/stages via work/out; a hit that
    # bypassed work/out would ship an empty package.
    data = _build_stage()
    steps = data["jobs"]["build"]["steps"]
    by_name = {s.get("name", ""): s for s in steps}
    use_cached = by_name["Use cached RPMs"]
    assert "work/out" in use_cached.get("run", ""), (
        "cache hits must land in work/out like fresh builds")


def test_resolve_and_build_share_the_dnf_cache():
    # Both container runs must mount the same libdnf5 cache dir (and ask
    # dnf to retain RPMs), or every job downloads its builddep set twice.
    data = _build_stage()
    steps = data["jobs"]["build"]["steps"]
    by_name = {s.get("name", ""): s for s in steps}
    for step in ("Resolve build root for cache key", "Build in Fedora container"):
        run = by_name[step].get("run", "")
        assert "work/dnf-cache:/var/cache/libdnf5" in run, (
            f"{step} is missing the shared dnf cache mount")
        assert "keepcache=1" in run, (
            f"{step} does not retain RPMs in the shared cache")


def test_shared_dnf_cache_has_a_single_weekly_writer():
    # Matrix jobs only RESTORE (70 parallel writers would thrash the 10GB
    # budget); exactly one scheduled job saves.
    data = _build_stage()
    steps = data["jobs"]["build"]["steps"]
    uses = [s.get("uses", "") for s in steps]
    assert any(u.startswith("actions/cache/restore@") for u in uses), (
        "build-stage does not restore the shared dnf cache")
    assert not any(u.startswith("actions/cache/save@") for u in uses), (
        "build-stage must never save: single-writer seed owns that")
    seed = yaml.safe_load((WORKFLOWS / "seed-dnf-cache.yml").read_text())
    # NOTE: bare `on:` parses as boolean True under YAML 1.1.
    triggers = seed.get("on", seed.get(True, {}))
    assert "schedule" in triggers, "seed job is not scheduled"
    seed_uses = [s.get("uses", "") for s in
                 seed["jobs"]["seed"]["steps"]]
    assert any(u.startswith("actions/cache/save@") for u in seed_uses), (
        "seed job does not save the shared dnf cache")


def _rebuild_pigeon_jobs():
    data = yaml.safe_load((WORKFLOWS / "rebuild-pigeon.yml").read_text())
    return data["jobs"]


def test_srpm_wave_gates_all_rebuilds():
    # The SRPM wave must finish before any binary wave starts: spec and
    # source errors fail here in ~1 min instead of hiding behind serial
    # stages and 10-minute compiles.
    jobs = _rebuild_pigeon_jobs()
    assert "srpm" in jobs, "no SRPM wave in rebuild-pigeon"
    assert "srpm" in jobs["rebuild0"].get("needs", []), (
        "rebuild0 does not wait for the SRPM wave (transitively gates all)")
    # The wave is a reusable workflow call, not an inline job: it delegates
    # to srpm.yml so the same build can run from packit-srpm-pilot.
    assert jobs["srpm"].get("uses", "").endswith("srpm.yml"), (
        "rebuild-pigeon srpm job must delegate to the reusable srpm.yml workflow")


def test_srpm_wave_builds_and_uploads_per_package_srpms():
    # The per-package steps live in the reusable srpm.yml workflow, not inline
    # in rebuild-pigeon.yml. Both halves must stay present.
    import yaml as _yaml
    srpm_wf = _yaml.safe_load((WORKFLOWS / "srpm.yml").read_text())
    srpm = srpm_wf["jobs"]["srpm"]
    steps = srpm.get("steps", []) or []
    by_name = {s.get("name", "") for s in steps}
    assert "Stage all sources for this package" in by_name, (
        "SRPM wave must stage sources through the shared action")
    assert "Build SRPM in Fedora container" in by_name, (
        "SRPM wave must run rpmbuild -bs")
    assert "Upload SRPM artifact" in by_name, (
        "SRPM wave must upload per-package SRPMs")
    # The reusable workflow takes the package list as an input and fans out
    # over it, so rebuild-pigeon can delegate without inlining the matrix.
    # NOTE: bare `on:` parses as boolean True under YAML 1.1.
    on_wf = srpm_wf.get("on", srpm_wf.get(True, {}))
    assert "packages" in on_wf["workflow_call"]["inputs"]
    assert "srpm-${{ matrix.package }}" in str(
        srpm_wf["jobs"]["srpm"]["steps"][-1].get("with", {}))


def test_build_stage_shares_source_staging_with_srpm_wave():
    # One source-staging implementation (composite action), used by both
    # lanes — never two copies drifting apart.
    data = _build_stage()
    steps = data["jobs"]["build"]["steps"]
    assert any(s.get("uses", "") == "./.github/actions/stage-sources"
               for s in steps), (
        "build-stage does not use the shared stage-sources action")
