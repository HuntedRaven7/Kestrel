"""Gate: specs must not hand-declare the cargo source tables %cargo_prep wrote.

Every rpm-factory package that vendors crates calls %cargo_prep (cargo-rpm-macros,
verified in a fedora:44 container). The macro writes into .cargo/config.toml:

- plain ``%cargo_prep``: ``[source.local-registry]`` plus
  ``[source.crates-io]`` with ``replace-with = "local-registry"``
- ``%cargo_prep -v DIR``: ``[source.vendored-sources]`` (directory = DIR)
  plus ``[source.crates-io]`` with ``replace-with = "vendored-sources"``

Re-declaring any of those tables in a spec heredoc produces invalid TOML
(``duplicate key``) and every cargo invocation in %build dies before
compiling anything. This bug class bit fish, waypipe and rust-just during
stage-2 rebuilds. To vendor crates, use ``%cargo_prep -v DIR`` or repoint
the existing ``replace-with`` key with sed — never append a second table.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ROOT / "rpm-factory" / "packages"

# Tables %cargo_prep always writes itself; a spec-side copy is a duplicate key.
MACRO_TABLES = ("[source.crates-io]", "[source.local-registry]")


def _strip_comments(text: str) -> str:
    """Drop `#` comment lines so prose about a construct isn't flagged."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _specs_with_cargo_prep() -> list[Path]:
    out = []
    for spec in sorted(PACKAGES.glob("*/*.spec")):
        if re.search(r"^%cargo_prep\b", spec.read_text(), re.M):
            out.append(spec)
    return out


CARGO_SPECS = _specs_with_cargo_prep()


def test_gate_covers_known_cargo_packages():
    """The gate must stay meaningful: the known cargo packages are scanned."""
    assert {"waypipe", "rust-just"} <= {s.parent.name for s in CARGO_SPECS}


@pytest.mark.parametrize("spec", CARGO_SPECS, ids=lambda p: p.parent.name)
def test_spec_does_not_redeclare_macro_written_tables(spec):
    """Re-declaring [source.crates-io] etc. makes the config invalid TOML."""
    body = _strip_comments(spec.read_text())
    for table in MACRO_TABLES:
        assert table not in body, (
            f"{spec.parent.name}: spec declares `{table}` but %cargo_prep "
            "already wrote it; cargo fails with 'duplicate key'. Repoint the "
            "existing key with sed or use `%cargo_prep -v DIR` instead"
        )


@pytest.mark.parametrize("spec", CARGO_SPECS, ids=lambda p: p.parent.name)
def test_spec_side_vendored_sources_are_consistent(spec):
    """A spec-declared vendored table must repoint crates-io away from the macro's local registry."""
    body = _strip_comments(spec.read_text())
    if "[source.vendored-sources]" not in body:
        pytest.skip("spec does not declare a vendored-sources table itself")
    # With `%cargo_prep -v DIR` the macro writes the vendored table; declaring
    # it again in the spec is a duplicate key.
    assert not re.search(r"^%cargo_prep\s+-v\b", body, re.M), (
        "%cargo_prep -v DIR already writes [source.vendored-sources]; "
        "declaring it again in the spec is a duplicate key"
    )
    # With plain %cargo_prep, crates-io still points at the local registry;
    # a spec-side vendored table only takes effect if replace-with is moved.
    assert re.search(
        r"s\|[^|\n]*local-registry[^|\n]*\|[^|\n]*vendored-sources", body
    ), (
        "crates-io still redirects to the macro's local-registry; repoint "
        "`replace-with` to vendored-sources (sed) or use `%cargo_prep -v DIR`"
    )