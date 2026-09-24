"""A cache hit must be indistinguishable from a build, or it is not safe.

RPM factory rebuilds every package on every run because its only skip mechanism
is the atomically-published consumer repository. tools/package_cache_key.py
is the key for a per-package GHCR cache answering "have we already built
this exact thing". The danger it has to avoid is serving an RPM built under
inputs that differ from this run's. So these tests are mostly about what
must *change* the key.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import package_cache_key as pck

BASE = dict(
    package="quickshell",
    recipe="recipe-digest",
    buildroot_digest="sha256:buildroot",
    factory_digest="",
    resolved_root=["gcc-16.2.1-1.fc44.x86_64", "glibc-2.42-1.fc44.x86_64"],
    disttag=".hum1.rpmfactory",
)

OCI_TAG = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$")


def test_identical_inputs_give_an_identical_key():
    assert pck.cache_key(**BASE) == pck.cache_key(**BASE)


def test_the_resolved_root_order_does_not_matter():
    """dnf reports installs in transaction order, which varies harmlessly."""
    reversed_root = dict(BASE, resolved_root=list(reversed(BASE["resolved_root"])))
    assert pck.cache_key(**BASE) == pck.cache_key(**reversed_root)


def test_a_duplicate_in_the_root_does_not_change_the_key():
    doubled = dict(BASE, resolved_root=BASE["resolved_root"] + BASE["resolved_root"])
    assert pck.cache_key(**BASE) == pck.cache_key(**doubled)


def test_every_input_changes_the_key():
    """The whole safety argument. A missed input serves a wrong RPM."""
    variants = {
        "package": dict(BASE, package="mango"),
        "recipe": dict(BASE, recipe="other-digest"),
        "buildroot": dict(BASE, buildroot_digest="sha256:other"),
        "disttag": dict(BASE, disttag=".hum2.rpmfactory"),
        "resolved_root": dict(
            BASE, resolved_root=["gcc-16.2.2-1.fc44.x86_64",
                                 "glibc-2.42-1.fc44.x86_64"]
        ),
    }
    base = pck.cache_key(**BASE)
    for field, variant in variants.items():
        assert pck.cache_key(**variant) != base, (
            f"changing {field} must change the key, or a cache hit can "
            f"serve an RPM built under different inputs"
        )


def test_the_schema_is_part_of_the_key():
    """An entry computed under older rules must not look current."""
    base = pck.cache_key(**BASE)
    original = pck.SCHEMA
    try:
        pck.SCHEMA = original + "-next"
        assert pck.cache_key(**BASE) != base
    finally:
        pck.SCHEMA = original


def _recipe(tmp_path, files: dict) -> str:
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return pck.recipe_digest(tmp_path)


def test_the_changelog_is_part_of_the_recipe(tmp_path):
    """%autorelease reads it, so it decides the Release and the NEVR."""
    a = _recipe(tmp_path, {"p.spec": b"spec", "changelog": b"* one\n"})
    b = _recipe(tmp_path, {"p.spec": b"spec", "changelog": b"* one\n* two\n"})
    assert a != b


def test_patches_and_sources_count(tmp_path):
    a = _recipe(tmp_path, {"p.spec": b"spec", "fix.patch": b"--- a\n"})
    b = _recipe(tmp_path, {"p.spec": b"spec", "fix.patch": b"--- b\n"})
    assert a != b


def test_a_rename_is_a_change(tmp_path):
    """Paths are hashed with contents, so moving a patch is not invisible."""
    a = _recipe(tmp_path, {"p.spec": b"spec", "one.patch": b"x"})
    b = _recipe(tmp_path, {"p.spec": b"spec", "two.patch": b"x"})
    assert a != b


def test_an_added_file_changes_it(tmp_path):
    a = _recipe(tmp_path, {"p.spec": b"spec"})
    b = _recipe(tmp_path, {"p.spec": b"spec", "extra.gpg": b"key"})
    assert a != b


def test_an_empty_recipe_is_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        pck.recipe_digest(tmp_path)


def test_a_real_recipe_hashes_stably():
    digest = pck.recipe_digest(pck.ROOT / "rpm-factory" / "packages" / "cpptrace")
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == pck.recipe_digest(pck.ROOT / "rpm-factory" / "packages" / "cpptrace")


def _run_cli(package="cpptrace", root_lines="gcc-1\nglibc-1\n"):
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        handle.write(root_lines)
        path = handle.name
    try:
        return subprocess.run(
            [sys.executable, str(pck.ROOT / "rpm-factory" / "tools" / "package_cache_key.py"),
             package, "--buildroot-digest", "sha256:aaa",
             "--disttag", ".hum1.rpmfactory", "--resolved-root", path],
            capture_output=True, text=True, cwd=pck.ROOT,
        )
    finally:
        Path(path).unlink()


def test_cli_prints_a_single_key():
    result = _run_cli()
    assert result.returncode == 0, result.stderr
    assert re.fullmatch(r"[0-9a-f]{32}", result.stdout.strip())
    assert len(result.stdout.strip().splitlines()) == 1


def test_cli_refuses_an_empty_resolved_root():
    """A key over nothing would collide across genuinely different roots."""
    result = _run_cli(root_lines="\n  \n")
    assert result.returncode == 1
    assert "refusing to compute a cache key" in result.stderr


def test_cli_rejects_an_unknown_package():
    result = _run_cli(package="does-not-exist")
    assert result.returncode == 1
    assert "no recipe at" in result.stderr


def test_a_key_is_always_a_valid_oci_tag():
    for i in range(200):
        key = pck.cache_key(**dict(BASE, recipe=f"recipe-{i}"))
        assert re.fullmatch(r"[0-9a-f]{32}", key)
        assert OCI_TAG.match(key)


def test_the_hash_binds_the_package_so_no_prefix_is_needed():
    keys = {name: pck.cache_key(**dict(BASE, package=name))
            for name in ("mango", "quickshell", "rofi", "foot")}
    assert len(set(keys.values())) == len(keys)


def test_a_tag_hostile_package_name_is_harmless():
    key = pck.cache_key(**dict(BASE, package="gtk+"))
    assert re.fullmatch(r"[0-9a-f]{32}", key)
    assert OCI_TAG.match(key)
