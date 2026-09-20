"""Tests for audit_sources.py handling of declared extra_sources.

Names declared in the lock's extra_sources are staged at build time by
source_pipeline.py fetch, so the audit must skip them (never report
MISSING, never attempt a dist-git fetch).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import audit_sources as au


def _setup(tmp_path, monkeypatch, spec_body: str, extras: list):
    root = tmp_path
    pkgdir = root / "pigeon" / "packages" / "widg"
    pkgdir.mkdir(parents=True)
    (pkgdir / "widg.spec").write_text(spec_body)
    data = {"packages": {"widg": {
        "version": "3",
        "url_template": "https://example.invalid/widg-{version}.tar.gz",
        "sha512": "0" * 128,
        "filename": "widg-3.tar.gz",
        "extra_sources": extras,
    }}}
    (root / "pigeon" / "config").mkdir(parents=True)
    (root / "pigeon" / "config" / "upstream-sources.json").write_text(
        json.dumps(data))
    monkeypatch.setattr(au, "ROOT", root)
    monkeypatch.setattr(au, "PKGS", root / "pigeon" / "packages")
    return pkgdir


SPEC = "Name: widg\nVersion: 3\nSource0: widg-3.tar.gz\nSource1: side-3.tar.gz\n"


def test_declared_extra_is_skipped(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, monkeypatch, SPEC, [{
        "filename": "side-3.tar.gz",
        "url_template": "https://example.invalid/side-3.tar.gz",
        "sha512": "0" * 128,
    }])
    assert au.audit(fix=True, only="widg") == 0
    assert "STILL MISSING" not in capsys.readouterr().out


def test_undeclared_name_still_missing(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, SPEC, [])
    assert au.audit(fix=False, only="widg") == 1


# --- spec_sources(): static pre-rpmbuild gate -----------------------------
#
# Regression cover for the pulseaudio SRPM failure: the spec declared a
# Source1 the pipeline never staged, so rpmbuild -bs died with
# "Bad file: .../pulseaudio-17.0.tar.xz.sha256sum: No such file or directory".


def _gate_setup(tmp_path, monkeypatch, spec_body: str, extras: list,
                committed: list[str] | None = None,
                on_disk_only: list[str] | None = None):
    pkgdir = _setup(tmp_path, monkeypatch, spec_body, extras)
    for name in committed or []:
        (pkgdir / name).write_text("x")
    for name in on_disk_only or []:
        (pkgdir / name).write_text("x")
    # Pretend only `committed` is tracked; anything else is a dev-only blob
    # (gitignored), which is absent from a CI checkout.
    monkeypatch.setattr(au, "committed_names",
                        lambda d: {p.name for p in d.iterdir()} & set(committed or []))
    monkeypatch.setattr(au, "staged_names",
                        lambda: {"widg": "widg-3.tar.gz"})
    return pkgdir


def test_spec_sources_flags_unstaged_source1(tmp_path, monkeypatch, capsys):
    """The exact pulseaudio bug: declared Source1, nothing stages it."""
    _gate_setup(tmp_path, monkeypatch, SPEC, [])
    assert au.spec_sources(only="widg") == 1
    out = capsys.readouterr().out
    assert "Bad file" in out
    assert "Source1 -> side-3.tar.gz" in out


def test_spec_sources_accepts_registered_extra(tmp_path, monkeypatch):
    _gate_setup(tmp_path, monkeypatch, SPEC, [{
        "filename": "side-3.tar.gz",
        "url_template": "https://example.invalid/side-3.tar.gz",
        "sha512": "0" * 128,
    }])
    assert au.spec_sources(only="widg") == 0


def test_spec_sources_rejects_uncommitted_on_disk_file(tmp_path, monkeypatch, capsys):
    """A gitignored blob present locally must NOT satisfy the gate: CI starts
    from a fresh checkout where it does not exist (the pulseaudio case)."""
    _gate_setup(tmp_path, monkeypatch, SPEC, [], on_disk_only=["side-3.tar.gz"])
    assert au.spec_sources(only="widg") == 1
    assert "NOT committed" in capsys.readouterr().out


def test_spec_sources_accepts_committed_file(tmp_path, monkeypatch):
    _gate_setup(tmp_path, monkeypatch, SPEC, [], committed=["side-3.tar.gz"])
    assert au.spec_sources(only="widg") == 0


def test_spec_sources_skips_literal_if0_source(tmp_path, monkeypatch):
    """openjpeg's `%if 0%{?runcheck} Source1: data.tar.xz %endif` is inactive
    unless runcheck is defined, so it must not be reported."""
    spec = ("Name: widg\nVersion: 3\nSource0: widg-3.tar.gz\n"
            "%if 0%{?runcheck}\nSource1: data.tar.xz\n%endif\n")
    _gate_setup(tmp_path, monkeypatch, spec, [])
    assert au.spec_sources(only="widg") == 0


def test_spec_sources_uses_else_branch(tmp_path, monkeypatch, capsys):
    """pulseaudio's shape: a dead %if branch plus a live %else branch. The
    %else Source1 is real and must be checked."""
    spec = ("Name: widg\nVersion: 3\n"
            "%if 0%{?gitrel}\nSource0: widg-3-g%{gitrev}.tar.xz\n%else\n"
            "Source0: widg-3.tar.gz\nSource1: side-3.tar.gz\n%endif\n")
    _gate_setup(tmp_path, monkeypatch, spec, [])
    assert au.spec_sources(only="widg") == 1
    assert "Source1 -> side-3.tar.gz" in capsys.readouterr().out


def test_spec_sources_resolves_conditional_version_macro(tmp_path, monkeypatch):
    """pulseaudio writes Version as %{pa_major}%{?pa_minor:.%{pa_minor}}; an
    unresolved %{ there used to make the gate skip the basename silently."""
    spec = ("%global pa_major 17.0\n#global pa_minor 0\n"
            "Name: widg\nVersion: %{pa_major}%{?pa_minor:.%{pa_minor}}\n"
            "Source0: https://example.invalid/widg-%{version}.tar.gz\n"
            "Source1: https://example.invalid/side-%{version}.tar.xz\n")
    _gate_setup(tmp_path, monkeypatch, spec, [])
    monkeypatch.setattr(au, "staged_names", lambda: {"widg": "widg-17.0.tar.gz"})
    assert au.spec_sources(only="widg") == 1


def test_spec_sources_allows_url_fragment_basename(tmp_path, monkeypatch):
    """adw-gtk3-theme style URL#/file: the basename comes from the fragment."""
    spec = ("Name: widg\nVersion: 3\nSource0: widg-3.tar.gz\n"
            "Source1: https://example.invalid/raw/README.md#/README.md.upstream\n")
    _gate_setup(tmp_path, monkeypatch, spec, [], committed=["README.md.upstream"])
    assert au.spec_sources(only="widg") == 0


def test_expand_handles_nested_shell_macro():
    """git's %{rcpath} nests %( ) inside %( ) and used to expand to garbage."""
    macros = {"version": "2.55.0", "real_version": "2.55.0",
              "rcpath": '%(test "%{version}" = "%{real_version}" || echo testing/)',
              "name": "git"}
    out = au.expand("%{rcpath}%{name}-%{real_version}.tar.sign", macros)
    assert out == "git-2.55.0.tar.sign"

