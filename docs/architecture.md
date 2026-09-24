# Architecture

Kestrel has one package factory and two consumers:

```text
verified source lock + RPM specs
              │
              ▼
      pinned Tine / Buck2 graph
      (Fedora 46 Rawhide)
              │
              ▼
 signed OCI RPM repository
          ╱          ╲
         ▼            ▼
     Warbler     Woodpecker
```

## RPM factory

`rpm-factory/` keeps recipes, sidecars, and `config/upstream-sources.json` as the source of truth.
`tools/stage_sources.py` fetches or generates each recipe's inputs, verifies locked bytes, and writes
a per-package tree under `rpm-factory/.tine-sources/`. `tools/tine_metadata.py` projects the Fedora 46
spec evaluation into generated `BUCK` and `config/tine-packages.json` files; those generated files are
checked by `just tine-check` and must not be edited by hand.

The GitHub build workflow invokes `.github/actions/tine-build` in package chunks. The action verifies
the exact `tine/` submodule commit, restores only a digest-verified pinned Buck2 executable and
recipe-keyed RPM outputs through `actions/cache`, builds the Tine targets, and prepares a candidate
repository image only after all chunks pass the publish gate. The candidate is scanned and attested
before the `latest` digest is promoted.

## Image consumers

Warbler and Woodpecker copy `/repository` from `ghcr.io/huntedraven7/rpm-factory` by OCI digest. Their
package contracts remain the installation allow-list; Fedora and Hummingbird repositories provide
bootstrap tooling and buildroot packages but are not treated as substitutes for factory recipes.

## Trust boundaries

- A recipe without an `upstream-sources.json` entry cannot build or publish.
- Staged archives must match their recorded SHA-512 before entering the Buck graph.
- The Tine submodule pointer and pinned Buck2 digest are verified before every CI build.
- Published repositories and images are signed, attested, scanned, and promoted only through their
  respective workflows.
