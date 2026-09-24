---
name: rpm-factory-packaging
description: RPM recipes, specs, Tine/Buck builds, source staging
---
# RPM factory packaging

Recipes live in `rpm-factory/packages/<name>/` (spec + patches + `.hummingbird-upstream.json`).
The specs and `rpm-factory/config/upstream-sources.json` remain authoritative. Tine is pinned as the
`tine` submodule and its generated projection lives in `rpm-factory/BUCK` plus
`rpm-factory/config/tine-packages.json`; regenerate it with `just tine-generate` after spec changes.

Build one package locally with `just tine-build <pkg>`. The GitHub workflow builds packages in
parallel chunks with the custom `.github/actions/tine-build` action. Tine emits binary and source
RPMs together; the old stage-artifact and separate SRPM lanes are retired.
