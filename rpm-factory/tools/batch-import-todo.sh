#!/usr/bin/env bash
# Batch import all TODO packages from Fedora dist-git

set -euo pipefail

PACKAGES=(
    xdg-desktop-portal-wlr
    xdg-desktop-portal-gtk
    seatd
    wl-clipboard
    grim
    slurp
    swayidle
    swaylock
    brightnessctl
    pamixer
    xfce-polkit
    polkit
    foot
    fwupd
    libinput
    libwacom
    libratbag
    iio-sensor-proxy
    ddcutil
    ModemManager
    tailscale
    wireguard-tools
    firewalld
    containerd
    runc
    crun
    podman
    skopeo
    buildah
    dracut
    grub2
    smartmontools
    nvme-cli
    pciutils
    hwdata
    libblockdev
    libbytesize
    udisks2
    upower
    bluez
    colord
    colord-gtk
    lcms2
    alsa-firmware
)

echo "Starting batch import of ${#PACKAGES[@]} packages..."

for pkg in "${PACKAGES[@]}"; do
    echo "========================================"
    echo "Importing $pkg..."
    echo "========================================"

    dest="rpm-factory/packages/$pkg"

    if [ -d "$dest" ]; then
        echo "Package $pkg already exists at $dest, skipping"
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

    cat > "$dest/.hummingbird-upstream.json" << EOF
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
    cd /
    rm -rf "$tmpdir"
done

echo "========================================"
echo "Batch import complete!"
echo "========================================"