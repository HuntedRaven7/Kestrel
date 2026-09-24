#!/usr/bin/env bash
# Bulk import and create specs for all packages in upstream-sources.json
# that don't have local specs yet.

set -euo pipefail

REPO_ROOT="/var/home/robin/git/Kestrel"
cd "$REPO_ROOT"

# Packages that already have local specs
HAVE_SPECS=(
    awww ghostty grim kestrel-gdm-config mango quickshell rofi scenefx seatd slurp
    wl-clipboard wlroots xdg-desktop-portal-gtk xdg-desktop-portal-wlr
)

# All packages from upstream-sources.json that need specs
NEED_SPECS=(
    ModemManager alsa-firmware bluez brightnessctl buildah colord colord-gtk
    containerd crun ddcutil dracut firewalld foot fwupd grub2 hwdata iio-sensor-proxy
    k0s kubeflex kubestellar kubestellar-console lcms2 libblockdev libbytesize
    libinput libratbag libwacom nvme-cli pamixer pciutils podman polkit runc skopeo
    smartmontools swayidle swaylock tailscale udisks2 upower wireguard-tools
    wlroots xfce-polkit
)

echo "Importing ${#NEED_SPECS[@]} packages from Fedora dist-git..."

for pkg in "${NEED_SPECS[@]}"; do
    echo "========================================"
    echo "Importing $pkg..."
    echo "========================================"

    dest="rpm-factory/packages/$pkg"

    if [ -d "$dest" ]; then
        echo "Package $pkg already exists, skipping"
        continue
    fi

    # Clone Fedora dist-git rawhide
    tmpdir=$(mktemp -d)
    if ! git clone "https://src.fedoraproject.org/rpms/$pkg.git" "$tmpdir/$pkg" --branch rawhide --depth 1 2>/dev/null; then
        echo "Failed to clone $pkg from rawhide, trying f44..."
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
echo "1. Run: python3 rpm-factory/tools/source_pipeline.py record <pkg> for each new package"
echo "2. Update .packit.yaml with new package entries"
echo "3. Run: just check && just test"