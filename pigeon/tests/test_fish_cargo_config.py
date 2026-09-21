"""Tests for fish.spec cargo configuration.

Regression cover for the fish build failure:

    error: failed to parse manifest at .../Cargo.toml
    Caused by: could not parse TOML configuration in .../.cargo/config.toml
    TOML parse error at line 35, column 9
      35 | [source.crates-io]
         |         ^^^^^^^^^
      duplicate key

%cargo_prep (cargo-rpm-macros) already emits a `[source.crates-io]` table
pointing at the local registry. The spec appended a second
`[source.crates-io]` header, which is invalid TOML, so every cargo invocation
in %build died before compiling anything.
"""
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "pigeon" / "packages" / "fish" / "fish.spec"


def _cargo_prep_config() -> str:
    """Stand-in for what %cargo_prep writes into .cargo/config.toml.

    Mirrors cargo-rpm-macros 6.0.x on Fedora 44 (verified via
    `rpm --eval '%cargo_prep'`): a local-registry source plus a crates-io
    source redirected to it.
    """
    return (
        '[build]\nrustc = "/usr/bin/rustc"\n'
        "\n"
        '[install]\nroot = "/builddir/usr"\n'
        "\n"
        "[source.local-registry]\n"
        'directory = "/usr/share/cargo/registry"\n'
        "\n"
        "[source.crates-io]\n"
        'registry = "https://crates.io"\n'
        'replace-with = "local-registry"\n'
        "\n"
    )


def _prep_appended_config() -> str:
    """The heredoc/tail of %prep that shapes cargo's source replacement."""
    text = SPEC.read_text()
    prep = text.split("%conf", 1)[0]
    # Everything from the `sed -i` repoint / heredoc onward.
    tail = prep.split("cat fishshell-cargo-config.toml >> .cargo/config.toml", 1)
    assert len(tail) == 2, "spec no longer appends the fish cargo config"
    return tail[1]


def _strip_spec_comments(text: str) -> str:
    """Drop `#` comments so prose about a construct isn't mistaken for it."""
    out = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def test_prep_does_not_redeclare_crates_io_table():
    """A second `[source.crates-io]` header makes the TOML invalid."""
    appended = _strip_spec_comments(_prep_appended_config())
    assert "[source.crates-io]" not in appended, (
        "fish %prep declares [source.crates-io] again; %cargo_prep already "
        "wrote that table and cargo will fail with 'duplicate key'"
    )


def test_prep_repoints_local_registry_to_vendored_sources():
    """cargo must resolve crates from the vendored dir, offline."""
    appended = _prep_appended_config()
    assert re.search(r's\|.*local-registry.*\|.*vendored-sources.*\|',
                     appended), (
        "fish %prep must sed `replace-with` from local-registry to "
        "vendored-sources, or cargo will look in /usr/share/cargo/registry"
    )
    assert "[source.vendored-sources]" in appended
    assert 'directory = "vendor"' in appended


def test_resulting_cargo_config_is_valid_toml():
    """End-to-end: cargo_prep output + spec additions must parse as TOML."""
    appended = _prep_appended_config()
    # Replay the spec's sed against cargo_prep's output.
    m = re.search(r"sed -i 's\|([^|]*)\|([^|]*)\|'", appended)
    assert m, "could not find the replace-with sed in fish %prep"
    pattern, repl = m.group(1), m.group(2)
    body = re.sub(pattern, repl, _cargo_prep_config(), flags=re.M)
    # Then everything inside the trailing heredoc.
    heredoc = re.search(r"<<'EOF'\n(.*?)\nEOF", appended, re.S)
    assert heredoc, "could not find the vendored-sources heredoc"
    body += "\n" + heredoc.group(1) + "\n"

    config = tomllib.loads(body)  # raises on duplicate keys
    assert config["source"]["crates-io"]["replace-with"] == "vendored-sources"
    assert config["source"]["vendored-sources"]["directory"] == "vendor"
    # The local-registry table %cargo_prep creates must still be intact.
    assert config["source"]["local-registry"]["directory"] == \
        "/usr/share/cargo/registry"
