import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rpm-factory" / "tools"))

import publish_gate as gate


def _metadata(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps({"packages": {
        "demo": {
            "package": "demo",
            "subpackages": ["demo-lib"],
        }
    }}))
    return path


def _rpm(path, name, release="1.hum1.rpmfactory", arch="x86_64"):
    path.write_bytes(b"rpm fixture")
    return name, "1", release, arch


def test_publish_requires_build_and_repository_gates():
    assert gate.publish_allowed(build_ok=True, repository_ok=True)
    assert not gate.publish_allowed(build_ok=False, repository_ok=True)
    assert not gate.publish_allowed(build_ok=True, repository_ok=False)


def test_repository_gate_requires_expected_binary_set(tmp_path, monkeypatch):
    metadata = _metadata(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    records = {}
    records[repo / "demo-1.x86_64.rpm"] = _rpm(
        repo / "demo-1.x86_64.rpm", "demo"
    )
    records[repo / "demo-lib-1.noarch.rpm"] = _rpm(
        repo / "demo-lib-1.noarch.rpm", "demo-lib", arch="noarch"
    )
    records[repo / "demo-1.src.rpm"] = _rpm(repo / "demo-1.src.rpm", "demo")
    monkeypatch.setattr(gate, "_rpm_record", lambda path: records[path])

    assert gate.check_repository(repo, metadata, ".hum1.rpmfactory")
    (repo / "demo-lib-1.noarch.rpm").unlink()
    assert not gate.check_repository(repo, metadata, ".hum1.rpmfactory")


def test_repository_gate_rejects_bad_suffix_and_unexpected_package(
    tmp_path, monkeypatch
):
    metadata = _metadata(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    records = {
        repo / "demo-1.x86_64.rpm": _rpm(
            repo / "demo-1.x86_64.rpm", "demo", release="1.fc46"
        ),
        repo / "demo-lib-1.noarch.rpm": _rpm(
            repo / "demo-lib-1.noarch.rpm", "demo-lib", arch="noarch"
        ),
        repo / "rogue-1.x86_64.rpm": _rpm(
            repo / "rogue-1.x86_64.rpm", "rogue"
        ),
    }
    monkeypatch.setattr(gate, "_rpm_record", lambda path: records[path])

    assert not gate.check_repository(repo, metadata, ".hum1.rpmfactory")


def test_repository_gate_rejects_empty_directory(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    assert not gate.check_repository(repo, _metadata(tmp_path), ".hum1.rpmfactory")
