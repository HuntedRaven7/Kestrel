#!/usr/bin/env python3
"""The tag under which one package's built RPMs are cached.

RPM factory's only skip mechanism is the published consumer repository, and
publication is atomic: it needs every stage, plus precedence, plus the
base-image transaction. So one red package freezes the repository, and
everything outside it rebuilds from scratch on every run — quickshell
alone costs ~10 minutes a build, with byte-identical inputs, run after run.

This is the other half of the answer: a cache that answers "have we
already built this exact thing", kept strictly separate from "is the
repository coherent enough to install from". Nothing installs from the
cache. A hit is materialised as this job's ordinary stage artifact, so
precedence and publish see an identical repository either way. That
property is what makes a hit safe to trust: it changes how the RPMs were
obtained, never what the run validates.

Why keying on the recipe alone would be wrong
---------------------------------------------
A stage-N package builds in a root containing earlier stages' fresh
output. A key over the spec alone would hand back an RPM linked against
different libraries than this run produced — precisely the incoherence
the publish gate exists to catch, arriving through the cache instead. So
the resolved build root is part of the key, and the key is therefore
computed *after* dnf has resolved builddep rather than before. That
costs the resolution (about a minute) and saves the compile.

Why the chain holds across runs
--------------------------------
It only works if an unchanged recipe yields an unchanged NEVR, or every
run's resolved root would differ from the last and nothing would ever
hit. It does: most specs hardcode `Release: <v>.hum1.rpmfactory`, and the
few using %autorelease (e.g. runc, containerd) derive it from committed
sources, not from a build counter.

Hashing whole files, comments included, is deliberate: it can only ever
rebuild something that did not need rebuilding, never reuse something
stale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Bumped when the meaning of the key changes, so an old cache entry computed
# under different rules can never be mistaken for a current one.
SCHEMA = "1"

# The tag is the key and nothing else. A 32-character hex digest always matches
# the OCI tag grammar ([a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}), so the tag can never
# be invalid and there is nothing to validate.
#
# The package name is inside the hash (see cache_key), never in the tag:
# RPM names are laxer than OCI tags, so a name prefix would mangle packages
# like `gtk+` into a permanent miss that reads as a correctness bug.
# Legibility is served where it is actually needed instead: the build log
# prints the package and the key it computed, and the push step labels the
# cache image so `skopeo inspect` answers "what is this entry" without a
# side database:
#
#     org.opencontainers.image.title      = <package>
#     org.opencontainers.image.version    = <nevr>
#     org.opencontainers.image.revision   = <the commit built from>
#     org.kestrel.rpm-factory.disttag          = <.hum1.rpmfactory>


def recipe_digest(package_dir: Path) -> str:
    """Every file in the recipe, by sorted relative path.

    Paths are hashed alongside contents so a rename is a change, and the
    directory is walked rather than globbed for *.spec so patches, the
    changelog, staged sources and keyrings all count. Staged tarballs are
    hash-verified downloads, deterministic for a given lock entry, so their
    presence can only ever force a rebuild, never a false hit.
    """
    digest = hashlib.sha256()
    files = sorted(
        (path for path in package_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(package_dir).as_posix(),
    )
    if not files:
        raise ValueError(f"no files under {package_dir}")
    for path in files:
        digest.update(path.relative_to(package_dir).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def normalise_root(nevras: list[str]) -> list[str]:
    """The resolved build root as a stable, order-independent list.

    dnf reports installs in transaction order, which varies between runs for
    reasons that do not change the result, so sorting is what makes the key
    stable. Duplicates collapse: the same NEVRA twice is the same root.
    """
    return sorted({item.strip() for item in nevras if item.strip()})


def cache_key(
    *,
    package: str,
    recipe: str,
    buildroot_digest: str,
    factory_digest: str,
    resolved_root: list[str],
    disttag: str,
) -> str:
    """The cache tag for one package built under one exact set of inputs.

    Every field changes what lands in the RPMs:
      package           -- the name, so two recipes cannot collide
      recipe            -- spec, patches, sources, changelog
      buildroot_digest  -- a different base image produces a different binary
      factory_digest    -- reserved: what the root could install from a
                           factory repo (empty: rpm-factory has none)
      resolved_root     -- what it actually installed, post-resolution
      disttag           -- .hum1.rpmfactory, which lands in the Release
    """
    payload = json.dumps(
        {
            "schema": SCHEMA,
            "package": package,
            "recipe": recipe,
            "buildroot": buildroot_digest,
            "factory": factory_digest,
            "root": normalise_root(resolved_root),
            "disttag": disttag,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()[:32]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("--buildroot-digest", required=True)
    parser.add_argument("--factory-digest", default="")
    parser.add_argument("--disttag", required=True)
    parser.add_argument(
        "--resolved-root",
        required=True,
        help="File of NEVRAs installed for builddep, one per line, or - for stdin",
    )
    args = parser.parse_args()

    package_dir = ROOT / "rpm-factory" / "packages" / args.package
    if not package_dir.is_dir():
        print(f"no recipe at {package_dir}", file=sys.stderr)
        return 1

    if args.resolved_root == "-":
        nevras = sys.stdin.read().splitlines()
    else:
        nevras = Path(args.resolved_root).read_text().splitlines()
    if not normalise_root(nevras):
        # An empty root means the resolution step did not report, and a key over
        # nothing would collide across genuinely different roots. Refuse rather
        # than emit a key that could serve a wrong RPM.
        print(
            "resolved build root is empty; refusing to compute a cache key",
            file=sys.stderr,
        )
        return 1

    key = cache_key(
        package=args.package,
        recipe=recipe_digest(package_dir),
        buildroot_digest=args.buildroot_digest,
        factory_digest=args.factory_digest,
        resolved_root=nevras,
        disttag=args.disttag,
    )
    print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
