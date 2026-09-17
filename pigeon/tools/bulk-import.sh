#!/usr/bin/env bash
# Bulk import packages from Fedora dist-git rawhide
# Usage: ./tools/bulk-import.sh <package-list.txt>
# Package list format: one package name per line, # for comments

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

PACKAGE_LIST="${1:-}"
if [ -z "$PACKAGE_LIST" ] || [ ! -f "$PACKAGE_LIST" ]; then
    echo "Usage: $0 <package-list.txt>"
    echo "Package list format: one package name per line, # for comments"
    exit 1
fi

# Read package list, skip comments and empty lines
packages=()
while IFS= read -r line; do
    line=$(echo "$line" | sed 's/#.*//' | xargs)
    [ -n "$line" ] && packages+=("$line")
done < "$PACKAGE_LIST"

echo "Found ${#packages[@]} packages to import"

for pkg in "${packages[@]}"; do
    echo "========================================"
    echo "Importing $pkg..."
    echo "========================================"

    dest="pigeon/packages/$pkg"

    if [ -d "$dest" ]; then
        echo "Package $pkg already exists at $dest, skipping"
        continue
    fi

    # Clone Fedora dist-git rawhide
    tmpdir=$(mktemp -d)
    if ! git clone "https://src.fedoraproject.org/rpms/$pkg.git" "$tmpdir/$pkg" --branch rawhide --depth 1 2>/dev/null; then
        echo "Failed to clone $pkg from Fedora dist-git, trying alternative..."
        if ! git clone "https://src.fedoraproject.org/rpms/$pkg.git" "$tmpdir/$pkg" --branch f44 --depth 1 2>/dev/null; then
            echo "ERROR: Could not clone $pkg from any branch"
            rm -rf "$tmpdir"
            continue
        fi
    fi

    # Create destination
    mkdir -p "$dest"

    # Copy spec and patches
    cp "$tmpdir/$pkg"/*.spec "$dest/" 2>/dev/null || true
    cp "$tmpdir/$pkg"/*.patch "$dest/" 2>/dev/null || true

    # Find the spec file
    spec=$(ls "$dest"/*.spec 2>/dev/null | head -1)
    if [ -z "$spec" ]; then
        echo "ERROR: No spec file found in $pkg"
        rm -rf "$tmpdir"
        continue
    fi

    # Extract version from spec
    version=$(rpmspec -q --queryformat "%{VERSION}" "$spec" 2>/dev/null | head -1)

    # Record upstream provenance
    cd "$tmpdir/$pkg"
    remote_url=$(git config --get remote.origin.url)
    commit=$(git rev-parse HEAD)
    tree=$(git rev-parse HEAD^{tree})
    commit_time=$(git log -1 --format=%ct HEAD)

    cat > "$REPO_ROOT/$dest/.hummingbird-upstream.json" << EOF
{
  "remote": "$remote_url",
  "commit": "$commit",
  "tree": "$tree",
  "time": $commit_time
}
EOF

    # Rename spec to match package name if needed
    spec_name=$(basename "$spec")
    if [ "$spec_name" != "$pkg.spec" ]; then
        mv "$dest/$spec_name" "$dest/$pkg.spec"
    fi

    echo "Imported $pkg version $version"

    # Clean up
    cd "$REPO_ROOT"
    rm -rf "$tmpdir"
done

echo "========================================"
echo "Bulk import complete!"
echo "========================================"
echo "Next steps:"
echo "1. Review imported packages in pigeon/packages/"
echo "2. Add entries to pigeon/config/upstream-sources.json"
echo "3. Update warbler/packages/warbler.toml and woodpecker/packages/woodpecker.toml"
echo "4. Run: just check && just test"