import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rpm-factory" / "tools"))

import validate


def _root(tmp_path, entries):
    (tmp_path / "rpm-factory" / "config").mkdir(parents=True)
    (tmp_path / "rpm-factory" / "packages" / "a").mkdir(parents=True)
    (tmp_path / "rpm-factory" / "config" / "upstream-sources.json").write_text(
        json.dumps({"packages": entries})
    )
    return tmp_path


def test_validate_accepts_matching_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(validate, "ROOT", _root(tmp_path, {
        "a": {"version": "1", "url_template": "https://x/a-{version}.tar.gz",
              "sha512": "0" * 128, "filename": "a-1.tar.gz"},
    }))
    assert validate.main() == 0


def test_validate_rejects_stale_filename(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(validate, "ROOT", _root(tmp_path, {
        "a": {"version": "1", "url_template": "https://x/a-{version}.tar.gz",
              "sha512": "0" * 128, "filename": "a-TODO.tar.gz"},
    }))
    assert validate.main() == 1
    assert "stale filename for a" in capsys.readouterr().out
