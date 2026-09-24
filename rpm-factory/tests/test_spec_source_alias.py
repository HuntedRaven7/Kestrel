"""Tests for spec_source_alias.py (Source0 basename aliasing)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from spec_source_alias import alias_source0


def _spec(tmp: Path, body: str) -> Path:
    p = tmp / "foo.spec"
    p.write_text(body)
    return p


def test_aliases_renamed_tarball(tmp_path):
    spec = _spec(tmp_path, "Name: foo\nVersion: 1.0\nSource0: foo-1.0.tar.gz\n")
    staged = tmp_path / "v1.0.tar.gz"
    staged.write_bytes(b"archive-bytes")
    out = tmp_path / "sources"
    out.mkdir()
    created = alias_source0(spec, out, staged)
    assert created == ["foo-1.0.tar.gz"]
    assert (out / "foo-1.0.tar.gz").read_bytes() == b"archive-bytes"


def test_no_alias_when_names_match(tmp_path):
    spec = _spec(tmp_path, "Name: foo\nVersion: 1.0\nSource0: foo-1.0.tar.gz\n")
    staged = tmp_path / "foo-1.0.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    assert alias_source0(spec, out, staged) == []


def test_secondary_sources_untouched(tmp_path):
    spec = _spec(
        tmp_path,
        "Name: foo\nVersion: 1.0\n"
        "Source0: v1.0.tar.gz\n"
        "Source1: foo-1.0-vendor.tar.zst\n",
    )
    staged = tmp_path / "v1.0.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    assert alias_source0(spec, out, staged) == []
    assert not (out / "foo-1.0-vendor.tar.zst").exists()


def test_unresolvable_macro_skipped(tmp_path):
    spec = _spec(tmp_path, "Name: foo\nVersion: 1.0\nSource0: %{gosource}\n")
    staged = tmp_path / "v1.0.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    assert alias_source0(spec, out, staged) == []


def test_recipe_files_never_shadowed(tmp_path):
    # tailscale-style: Source0 is a service file the recipe provides.
    spec = _spec(tmp_path, "Name: foo\nVersion: 1.0\nSource0: foo.service\n")
    recipe = tmp_path / "recipe"
    recipe.mkdir()
    (recipe / "foo.service").write_text("unit")
    staged = tmp_path / "v1.0.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    assert alias_source0(spec, out, staged, recipe) == []
    assert not (out / "foo.service").exists()


def test_version_no_tilde_default(tmp_path):
    spec = _spec(
        tmp_path,
        "Name: nvme-cli\nVersion: 2.16\n"
        "Source0: %{url}/archive/v%{version_no_tilde}/%{name}-%{version_no_tilde}.tar.gz\n",
    )
    staged = tmp_path / "v2.16.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    created = alias_source0(spec, out, staged)
    assert created == ["nvme-cli-2.16.tar.gz"]


def test_conditional_double_source0(tmp_path):
    # libinput-style: snapshot branch (inactive) + release branch.
    spec = _spec(
        tmp_path,
        "Name: libinput\nVersion: 1.32.0\n"
        "%if 0%{?gitdate}\nSource0: libinput-%{gitdate}.tar.xz\n%else\n"
        "Source0: https://example.com/libinput-1.32.0.tar.bz2\n%endif\n",
    )
    staged = tmp_path / "libinput-1.32.0.tar.gz"
    staged.write_bytes(b"x")
    out = tmp_path / "sources"
    out.mkdir()
    created = alias_source0(spec, out, staged)
    assert created == ["libinput-1.32.0.tar.bz2"]
    assert (out / "libinput-1.32.0.tar.bz2").read_bytes() == b"x"
