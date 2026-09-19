import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

import validate_packit_config as vpc


def _setup(tmp_path, packages: dict, packit_packages: dict, spec_dirs: list[str]):
    (tmp_path / "pigeon" / "config").mkdir(parents=True)
    pkgs_dir = tmp_path / "pigeon" / "packages"
    pkgs_dir.mkdir(parents=True)
    for d in spec_dirs:
        (pkgs_dir / d).mkdir(parents=True)
        (pkgs_dir / d / f"{d}.spec").write_text("Name: test\nVersion: 1\n")
    (tmp_path / "pigeon" / "config" / "upstream-sources.json").write_text(
        json.dumps({"packages": packages})
    )
    (tmp_path / ".packit.yaml").write_text(
        yaml_safe_dump({"packages": packit_packages})
    )
    return tmp_path


def yaml_safe_dump(data):
    import yaml
    return yaml.dump(data, sort_keys=False, width=120)


def test_validate_packit_ok(tmp_path, monkeypatch):
    root = _setup(tmp_path,
        packages={"a": {"version": "1"}, "b": {"version": "1", "srpm": "rpmbuild"}},
        packit_packages={"a": {"specfile_path": "a.spec", "paths": ["pigeon/packages/a"]}},
        spec_dirs=["a"]
    )
    monkeypatch.setattr(vpc, "ROOT", root)
    monkeypatch.setattr(vpc, "PACKIT_YAML", root / ".packit.yaml")
    monkeypatch.setattr(vpc, "SOURCES_JSON", root / "pigeon" / "config" / "upstream-sources.json")
    monkeypatch.setattr(vpc, "PKGS_DIR", root / "pigeon" / "packages")
    assert vpc.main() == 0


def test_validate_packit_rpmbuild_in_packit_yaml(tmp_path, monkeypatch, capsys):
    root = _setup(tmp_path,
        packages={"a": {"version": "1", "srpm": "rpmbuild"}},
        packit_packages={"a": {"specfile_path": "a.spec", "paths": ["pigeon/packages/a"]}},
        spec_dirs=["a"]
    )
    monkeypatch.setattr(vpc, "ROOT", root)
    monkeypatch.setattr(vpc, "PACKIT_YAML", root / ".packit.yaml")
    monkeypatch.setattr(vpc, "SOURCES_JSON", root / "pigeon" / "config" / "upstream-sources.json")
    monkeypatch.setattr(vpc, "PKGS_DIR", root / "pigeon" / "packages")
    assert vpc.main() == 1
    assert "rpmbuild/local packages in .packit.yaml" in capsys.readouterr().err


def test_validate_packit_missing_from_packit_yaml(tmp_path, monkeypatch, capsys):
    root = _setup(tmp_path,
        packages={"a": {"version": "1"}},
        packit_packages={},
        spec_dirs=["a"]
    )
    monkeypatch.setattr(vpc, "ROOT", root)
    monkeypatch.setattr(vpc, "PACKIT_YAML", root / ".packit.yaml")
    monkeypatch.setattr(vpc, "SOURCES_JSON", root / "pigeon" / "config" / "upstream-sources.json")
    monkeypatch.setattr(vpc, "PKGS_DIR", root / "pigeon" / "packages")
    assert vpc.main() == 1
    assert "packages with specs missing from .packit.yaml" in capsys.readouterr().err


def test_validate_packit_extra_in_packit_yaml(tmp_path, monkeypatch, capsys):
    root = _setup(tmp_path,
        packages={},
        packit_packages={"a": {"specfile_path": "a.spec", "paths": ["pigeon/packages/a"]}},
        spec_dirs=[]
    )
    monkeypatch.setattr(vpc, "ROOT", root)
    monkeypatch.setattr(vpc, "PACKIT_YAML", root / ".packit.yaml")
    monkeypatch.setattr(vpc, "SOURCES_JSON", root / "pigeon" / "config" / "upstream-sources.json")
    monkeypatch.setattr(vpc, "PKGS_DIR", root / "pigeon" / "packages")
    assert vpc.main() == 1
    assert "packages in .packit.yaml without spec dir" in capsys.readouterr().err


def test_validate_packit_local_in_packit_yaml(tmp_path, monkeypatch, capsys):
    root = _setup(tmp_path,
        packages={"a": {"version": "1", "local": True}},
        packit_packages={"a": {"specfile_path": "a.spec", "paths": ["pigeon/packages/a"]}},
        spec_dirs=["a"]
    )
    monkeypatch.setattr(vpc, "ROOT", root)
    monkeypatch.setattr(vpc, "PACKIT_YAML", root / ".packit.yaml")
    monkeypatch.setattr(vpc, "SOURCES_JSON", root / "pigeon" / "config" / "upstream-sources.json")
    monkeypatch.setattr(vpc, "PKGS_DIR", root / "pigeon" / "packages")
    assert vpc.main() == 1
    assert "rpmbuild/local packages in .packit.yaml" in capsys.readouterr().err