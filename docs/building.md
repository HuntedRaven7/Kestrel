# Building

The package factory is built with the pinned Tine submodule. Tine uses its Fedora 46 Rawhide
snapshot and emits both binary and source RPMs.

```sh
git submodule update --init --recursive
just check          # source-lock, version, and source-reference checks
just test           # Python unit tests
just tine-check     # regenerate/check the F46 Tine projection
just tine-build pkg # stage sources and build one package locally
```

For a complete factory build, run the `rebuild-rpm-factory.yml` GitHub workflow. It builds the
package set in parallel chunks, caches pinned Buck2 and verified RPM outputs with `actions/cache`,
and publishes the signed OCI repository only from `main`.
