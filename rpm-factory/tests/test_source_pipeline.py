import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rpm-factory" / "tools"))

import source_pipeline as sp
import stage_sources as ss
import tine_metadata


def test_fetch_refuses_unknown_package(capsys):
    assert sp.cmd_fetch("no-such-pkg", None) == 1
    assert "no upstream-sources.json entry" in capsys.readouterr().out


def test_fetch_refuses_unversioned_package(tmp_path, monkeypatch, capsys):
    # A source entry with no agreed version/URL must refuse without network.
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "future": {"version": "TODO", "url_template": "TODO-x", "sha512": "TODO"},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.cmd_fetch("future", None) == 1
    assert "not fetchable" in capsys.readouterr().out
    assert sp.cmd_record("future", None) == 1


def test_local_package_needs_no_fetch(tmp_path, monkeypatch, capsys):
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "filepkg": {"version": "1", "local": True},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.cmd_fetch("filepkg", None) == 0
    assert sp.cmd_record("filepkg", None) == 0


def test_generated_local_source_must_match_lock(tmp_path):
    source = tmp_path / "generated-1.tar.gz"
    source.write_bytes(b"locked generated source")
    digest = hashlib.sha512(source.read_bytes()).hexdigest()
    ss._verify_locked_source("generated", source, digest)
    with pytest.raises(SystemExit, match="generated source has no recorded SHA-512"):
        ss._verify_locked_source("generated", source, "")
    with pytest.raises(SystemExit, match="generated source SHA-512 mismatch"):
        ss._verify_locked_source("generated", source, "0" * 128)


def test_tine_metadata_ignores_rename_commit_for_source_epoch(monkeypatch):
    history = (
        f"{'a' * 40}\t200\n\n"
        "R087\told/spec\tnew/spec\n"
        f"{'b' * 40}\t100\n\n"
        "M\told/spec\n"
    )
    monkeypatch.setattr(tine_metadata, "_run", lambda *args, **kwargs: history)

    assert tine_metadata._history_timestamp("new/spec") == 100


def test_stage_refreshes_existing_recipe_sidecars(tmp_path, monkeypatch):
    factory = tmp_path / "rpm-factory"
    recipe = factory / "packages" / "demo"
    recipe.mkdir(parents=True)
    (recipe / "demo.spec").write_text("Name: demo\n")
    archive = recipe / "demo-1.tar.gz"
    archive.write_bytes(b"locked")
    (recipe / "metadata.patch").write_text("new metadata\n")

    staged = tmp_path / "staged" / "demo"
    staged.mkdir(parents=True)
    (staged / "demo-1.tar.gz").write_bytes(b"locked")
    (staged / "metadata.patch").write_text("stale metadata\n")
    (staged / "obsolete.input").write_text("stale input\n")

    monkeypatch.setattr(ss, "FACTORY", factory)
    monkeypatch.setattr(ss, "TOOLS", factory / "tools")
    monkeypatch.setattr(ss, "SOURCES", {
        "demo": {
            "version": "1",
            "local": True,
            "filename": archive.name,
            "sha512": hashlib.sha512(archive.read_bytes()).hexdigest(),
        }
    })
    monkeypatch.setattr(ss, "_run", lambda *args, **kwargs: None)

    ss._stage_one("demo", tmp_path / "staged")

    assert (staged / "metadata.patch").read_text() == "new metadata\n"
    assert not (staged / "obsolete.input").exists()


def test_source_less_local_package_is_staged(tmp_path, monkeypatch):
    factory = tmp_path / "rpm-factory"
    recipe = factory / "packages" / "local-only"
    recipe.mkdir(parents=True)
    (recipe / "local-only.spec").write_text("Name: local-only\n")

    monkeypatch.setattr(ss, "FACTORY", factory)
    monkeypatch.setattr(ss, "TOOLS", factory / "tools")
    monkeypatch.setattr(ss, "SOURCES", {
        "local-only": {"version": "1", "local": True}
    })
    monkeypatch.setattr(ss, "_run", lambda *args, **kwargs: None)

    output = tmp_path / "staged"
    ss._stage_one("local-only", output)

    assert (output / "local-only").is_dir()


def test_entry_ready_gate():
    assert sp.entry_ready({"local": True}) is None
    assert sp.entry_ready({"version": "TODO"}) is not None
    assert sp.entry_ready({"version": "1", "url_template": "TODO-x"}) is not None
    assert sp.entry_ready({"version": "1", "url_template": "https://x/{version}.tar.gz"}) is None


def test_signature_dormant_without_config(tmp_path):
    result = sp.verify_signature({}, tmp_path / "a.tar.gz", tmp_path)
    assert result == {"checked": False, "reason": "no signature configured"}


def _staged_sources(tmp_path, monkeypatch, payload: bytes, sha512: str):
    archive = tmp_path / "fake-1.tar.gz"
    archive.write_bytes(payload)
    sources = {
        "packages": {
            "fake": {
                "version": "1",
                # file:// URL with {version} placeholder pointing at the staged archive.
                "url_template": f"file://{tmp_path}/fake-{{version}}.tar.gz",
                "sha512": sha512,
            }
        }
    }
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps(sources))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")


def test_fetch_verifies_staged_archive(tmp_path, monkeypatch):
    import gzip
    payload = gzip.compress(b"kestrel-test-payload")
    _staged_sources(tmp_path, monkeypatch, payload, hashlib.sha512(payload).hexdigest())
    assert sp.cmd_fetch("fake", None) == 0
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is True


def test_fetch_fails_closed_on_digest_mismatch(tmp_path, monkeypatch, capsys):
    import gzip
    _staged_sources(tmp_path, monkeypatch, gzip.compress(b"real-bytes"), "0" * 128)
    assert sp.cmd_fetch("fake", None) == 1
    assert "verification failed" in capsys.readouterr().out
    report = json.loads((tmp_path / "reports" / "fake.json").read_text())
    assert report["ok"] is False


def _vendored_setup(tmp_path, monkeypatch, payload: bytes, digest: str | None):
    pkgdir = tmp_path / "rpm-factory" / "packages" / "gated"
    pkgdir.mkdir(parents=True)
    (pkgdir / "gated-1.tar.gz").write_bytes(payload)
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {
        "gated": {"version": "1",
                  "url_template": "https://example.invalid/gated-{version}.tar.gz",
                  "sha512": digest if digest is not None else "TODO",
                  "vendored": True, "filename": "gated-1.tar.gz"},
    }}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sp, "ROOT", tmp_path)


def test_vendored_fetch_verifies_committed_bytes(tmp_path, monkeypatch):
    import gzip
    payload = gzip.compress(b"gated-payload")
    _vendored_setup(tmp_path, monkeypatch, payload, hashlib.sha512(payload).hexdigest())
    assert sp.cmd_fetch("gated", None) == 0


def test_vendored_fetch_fails_on_mismatch(tmp_path, monkeypatch, capsys):
    import gzip
    _vendored_setup(tmp_path, monkeypatch, gzip.compress(b"bytes"), "0" * 128)
    assert sp.cmd_fetch("gated", None) == 1
    assert "verification failed" in capsys.readouterr().out


def test_vendored_fetch_verifies_declared_extras(tmp_path, monkeypatch):
    import gzip
    primary = gzip.compress(b"primary")
    _vendored_setup(
        tmp_path,
        monkeypatch,
        primary,
        hashlib.sha512(primary).hexdigest(),
    )
    extra = tmp_path / "rpm-factory" / "packages" / "gated" / "gated-vendor.tar.bz2"
    payload = gzip.compress(b"vendor")
    extra.write_bytes(payload)
    registry = json.loads(sp.SOURCES.read_text())
    registry["packages"]["gated"]["extra_sources"] = [{
        "filename": extra.name,
        "vendored": True,
        "sha512": hashlib.sha512(payload).hexdigest(),
    }]
    sp.SOURCES.write_text(json.dumps(registry))
    output = tmp_path / "output"

    assert sp.cmd_fetch("gated", str(output)) == 0
    assert (output / extra.name).read_bytes() == payload

    extra.write_bytes(b"tampered")
    assert sp.cmd_fetch("gated", str(output)) == 1


def test_vendored_record_locks_committed_bytes(tmp_path, monkeypatch):
    import gzip
    payload = gzip.compress(b"gated-payload")
    _vendored_setup(tmp_path, monkeypatch, payload, "TODO")
    # record path needs a digest placeholder that passes the TODO gate:
    # use the vendored record flow directly via cmd_record after staging.
    srcfile = tmp_path / "upstream-sources.json"
    data = json.loads(srcfile.read_text())
    data["packages"]["gated"]["sha512"] = "0" * 128
    srcfile.write_text(json.dumps(data))
    assert sp.cmd_record("gated", None) == 0
    locked = json.loads(srcfile.read_text())["packages"]["gated"]["sha512"]
    assert locked == hashlib.sha512(payload).hexdigest()


def test_check_archive_refuses_html(tmp_path):
    page = tmp_path / "wall.html"
    page.write_text("<!DOCTYPE html><html><body>Sign in</body></html>")
    reason = sp.check_archive(page)
    assert reason is not None and "HTML" in reason


def test_check_archive_accepts_gzip(tmp_path):
    import gzip
    arc = tmp_path / "a.tar.gz"
    arc.write_bytes(gzip.compress(b"data"))
    assert sp.check_archive(arc) is None


# --- Tests for check_source ---


def _setup_sources(tmp_path, monkeypatch, packages: dict):
    """Helper to set up sources file and monkeypatch module paths."""
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": packages}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")


def test_check_source_unknown_package(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {"a": {"version": "1"}})
    assert sp.check_source("no-such-pkg") is False
    assert "no upstream-sources.json entry" in capsys.readouterr().out


def test_check_source_local_package(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {"localpkg": {"version": "1", "local": True}})
    assert sp.check_source("localpkg") is True  # local packages are considered "ready"
    assert "local package" in capsys.readouterr().out


def test_check_source_ready_package(tmp_path, monkeypatch, capsys):
    digest = "0" * 128
    _setup_sources(tmp_path, monkeypatch, {
        "ready": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                  "sha512": digest, "filename": "pkg.tar.gz"}
    })
    assert sp.check_source("ready") is True
    assert "ready for fetch" in capsys.readouterr().out


def test_check_source_local_package_passes(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {"localpkg": {"version": "1", "local": True}})
    assert sp.cmd_check("localpkg") == 0
    assert "local package" in capsys.readouterr().out


def test_check_source_no_version(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {
        "unversioned": {"url_template": "https://x/{version}/pkg.tar.gz", "sha512": "0" * 128}
    })
    assert sp.check_source("unversioned") is False
    assert "not ready" in capsys.readouterr().out


def test_check_source_no_digest(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {
        "nodigest": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz"}
    })
    assert sp.check_source("nodigest") is False
    assert "no recorded digest" in capsys.readouterr().out


def test_check_source_handles_malformed_json(tmp_path, monkeypatch):
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text("{invalid json")
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.check_source("pkg") is False


# --- Tests for validate_upstream_sources ---


def test_validate_accepts_valid_entries():
    data = {"packages": {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                "sha512": "0" * 128, "filename": "pkg.tar.gz"}
    }}
    assert sp.validate_upstream_sources(data) == []


def test_validate_rejects_stale_filename():
    data = {"packages": {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg-1.0.tar.gz",
                "sha512": "0" * 128, "filename": "pkg-TODO.tar.gz"}
    }}
    errors = sp.validate_upstream_sources(data)
    assert any("stale filename" in e for e in errors)


def test_validate_rejects_missing_version():
    data = {"packages": {
        "pkg": {"url_template": "https://x/{version}/pkg.tar.gz", "sha512": "0" * 128}
    }}
    errors = sp.validate_upstream_sources(data)
    assert any("version" in e for e in errors)


def test_validate_rejects_missing_sha512():
    data = {"packages": {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz"}
    }}
    errors = sp.validate_upstream_sources(data)
    assert any("sha512" in e for e in errors)


def test_validate_skips_local_packages():
    data = {"packages": {
        "localpkg": {"version": "1", "local": True}
    }}
    assert sp.validate_upstream_sources(data) == []


def test_validate_rejects_placeholder_url():
    data = {"packages": {
        "pkg": {"version": "1.0", "url_template": "TODO", "sha512": "0" * 128}
    }}
    errors = sp.validate_upstream_sources(data)
    assert any("url_template" in e for e in errors)


def test_cmd_validate_passes_with_valid_data(tmp_path, monkeypatch, capsys):
    digest = "0" * 128
    _setup_sources(tmp_path, monkeypatch, {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                "sha512": digest, "filename": "pkg.tar.gz"}
    })
    assert sp.cmd_validate() == 0
    assert "validated 1 source entries" in capsys.readouterr().out


def test_cmd_validate_fails_with_stale_filename(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg-1.0.tar.gz",
                "sha512": "0" * 128, "filename": "pkg-TODO.tar.gz"}
    })
    assert sp.cmd_validate() == 1
    assert "stale filename" in capsys.readouterr().out


def test_cmd_validate_handles_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, "SOURCES", tmp_path / "nonexistent.json")
    assert sp.cmd_validate() == 1


def test_cmd_validate_handles_malformed_json(tmp_path, monkeypatch):
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text("{invalid json")
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    assert sp.cmd_validate() == 1


# --- Tests for extra_sources (declared secondary inputs) ---


def _extras_setup(tmp_path, monkeypatch, primary: bytes, extra: bytes,
                  extra_sha: str | None):
    import gzip
    main_arc = tmp_path / "main-2.tar.gz"
    main_arc.write_bytes(gzip.compress(primary))
    side_arc = tmp_path / "side-2.tar.gz"
    side_arc.write_bytes(gzip.compress(extra))
    pkg = {
        "version": "2",
        "url_template": f"file://{tmp_path}/main-{{version}}.tar.gz",
        "sha512": hashlib.sha512(gzip.compress(primary)).hexdigest(),
        "filename": "main-2.tar.gz",
        # Declared staged name is decoupled from the URL basename.
        "extra_sources": [{
            "filename": "sidecar.tar.gz",
            "url_template": f"file://{tmp_path}/side-{{version}}.tar.gz",
            "sha512": extra_sha if extra_sha is not None else "TODO-re-record",
        }],
    }
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {"multi": pkg}}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sp, "ROOT", tmp_path)
    (tmp_path / "rpm-factory" / "packages" / "multi").mkdir(parents=True)


def test_fetch_stages_declared_extras(tmp_path, monkeypatch):
    import gzip
    _extras_setup(tmp_path, monkeypatch, b"main", b"side",
                  hashlib.sha512(gzip.compress(b"side")).hexdigest())
    out = tmp_path / "out"
    assert sp.cmd_fetch("multi", str(out), "rpm-factory/packages") == 0
    assert (out / "main-2.tar.gz").is_file()
    assert (out / "sidecar.tar.gz").is_file()
    assert (tmp_path / "rpm-factory" / "packages" / "multi" / "sidecar.tar.gz").is_file()
    report = json.loads((tmp_path / "reports" / "multi.json").read_text())
    assert report["ok"] is True
    assert report["extra_sources"][0]["ok"] is True


def test_fetch_fails_on_required_extra_mismatch(tmp_path, monkeypatch, capsys):
    _extras_setup(tmp_path, monkeypatch, b"main", b"side", "0" * 128)
    assert sp.cmd_fetch("multi", None) == 1
    out = capsys.readouterr().out
    assert "digest mismatch" in out
    assert "FAIL: extra sidecar.tar.gz" in out
    assert "FAIL: required extra_sources failed" in out


def test_fetch_warns_on_sidecar_extra_mismatch(tmp_path, monkeypatch, capsys):
    import gzip
    main_arc = tmp_path / "main-2.tar.gz"
    main_arc.write_bytes(gzip.compress(b"main"))
    side = tmp_path / "side.sha256sum"
    side.write_text("deadbeef  main-2.tar.gz\n")
    pkg = {
        "version": "2",
        "url_template": f"file://{tmp_path}/main-{{version}}.tar.gz",
        "sha512": hashlib.sha512(gzip.compress(b"main")).hexdigest(),
        "filename": "main-2.tar.gz",
        "extra_sources": [{
            "filename": "side.sha256sum",
            "url_template": f"file://{tmp_path}/side.sha256sum",
            "sha512": "0" * 128,
        }],
    }
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {"multi": pkg}}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sp, "ROOT", tmp_path)
    (tmp_path / "rpm-factory" / "packages" / "multi").mkdir(parents=True)
    assert sp.cmd_fetch("multi", None) == 0
    out = capsys.readouterr().out
    assert "WARN: extra side.sha256sum" in out
    assert "OK: multi@2 verified" in out


def test_fetch_stages_vendored_extra(tmp_path, monkeypatch):
    import gzip
    main_arc = tmp_path / "main-2.tar.gz"
    main_arc.write_bytes(gzip.compress(b"main"))
    pkg_dir = tmp_path / "rpm-factory" / "packages" / "multi"
    pkg_dir.mkdir(parents=True)
    vendor = pkg_dir / "vendor.tar.gz"
    vendor.write_bytes(gzip.compress(b"vendor-bytes"))
    pkg = {
        "version": "2",
        "url_template": f"file://{tmp_path}/main-{{version}}.tar.gz",
        "sha512": hashlib.sha512(gzip.compress(b"main")).hexdigest(),
        "filename": "main-2.tar.gz",
        "extra_sources": [{
            "filename": "vendor.tar.gz",
            "vendored": True,
            "sha512": hashlib.sha512(gzip.compress(b"vendor-bytes")).hexdigest(),
        }],
    }
    srcfile = tmp_path / "upstream-sources.json"
    srcfile.write_text(json.dumps({"packages": {"multi": pkg}}))
    monkeypatch.setattr(sp, "SOURCES", srcfile)
    monkeypatch.setattr(sp, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sp, "ROOT", tmp_path)
    out = tmp_path / "out"
    assert sp.cmd_fetch("multi", str(out)) == 0
    assert (out / "vendor.tar.gz").is_file()
    report = json.loads((tmp_path / "reports" / "multi.json").read_text())
    assert report["extra_sources"][0]["ok"] is True
    assert report["extra_sources"][0].get("vendored") is True


def test_record_locks_extras(tmp_path, monkeypatch):
    import gzip
    _extras_setup(tmp_path, monkeypatch, b"main", b"side", "TODO-re-record")
    assert sp.cmd_record("multi", None) == 0
    locked = json.loads((tmp_path / "upstream-sources.json").read_text())
    assert locked["packages"]["multi"]["extra_sources"][0]["sha512"] == \
        hashlib.sha512(gzip.compress(b"side")).hexdigest()


def test_verify_staged_checks_extras(tmp_path, monkeypatch, capsys):
    import gzip
    _extras_setup(tmp_path, monkeypatch, b"main", b"side",
                  hashlib.sha512(gzip.compress(b"side")).hexdigest())
    # Primary staged, extra missing, no stage-into healing -> refuse.
    (tmp_path / "rpm-factory" / "packages" / "multi" / "main-2.tar.gz").write_bytes(
        gzip.compress(b"main"))
    assert sp.cmd_fetch("multi", None, None, True) == 1
    assert "staged extra" in capsys.readouterr().out


def test_validate_rejects_extra_without_digest():
    data = {"packages": {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                "sha512": "0" * 128, "filename": "pkg.tar.gz",
                "extra_sources": [{"filename": "side.tar.gz",
                                   "url_template": "https://x/side.tar.gz"}]}
    }}
    errors = sp.validate_upstream_sources(data)
    assert any("extra_sources[0]" in e for e in errors)


def test_check_refuses_unrecorded_extra(tmp_path, monkeypatch, capsys):
    _extras_setup(tmp_path, monkeypatch, b"main", b"side", "TODO-re-record")
    assert sp.cmd_check("multi") == 1
    assert "no recorded digest" in capsys.readouterr().out


# --- Tests for CLI integration ---


def test_main_validate_command(tmp_path, monkeypatch, capsys):
    digest = "0" * 128
    _setup_sources(tmp_path, monkeypatch, {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                "sha512": digest, "filename": "pkg.tar.gz"}
    })
    assert sp.main(["validate"]) == 0
    assert "validated 1 source entries" in capsys.readouterr().out


def test_main_check_command(tmp_path, monkeypatch, capsys):
    digest = "0" * 128
    _setup_sources(tmp_path, monkeypatch, {
        "pkg": {"version": "1.0", "url_template": "https://x/{version}/pkg.tar.gz",
                "sha512": digest, "filename": "pkg-1.0.tar.gz"}
    })
    assert sp.main(["check", "pkg"]) == 0
    assert "ready for fetch" in capsys.readouterr().out


def test_main_check_unknown_package(tmp_path, monkeypatch, capsys):
    _setup_sources(tmp_path, monkeypatch, {"other": {"version": "1"}})
    assert sp.main(["check", "pkg"]) == 1
    assert "no upstream-sources.json entry" in capsys.readouterr().out
