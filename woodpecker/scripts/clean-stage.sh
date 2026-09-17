#!/usr/bin/env bash
# Clean build stage: remove build deps, caches, temp files

set -euo pipefail

echo "Cleaning build stage..."

# Remove build dependencies (keep only runtime)
dnf remove -y \
    createrepo_c \
    python3-dnf \
    python3-hawkey \
    rpm-build \
    rpmdevtools \
    mock \
    gcc \
    meson \
    ninja-build \
    cmake \
    pkgconf \
    pkgconf-pkg-config \
    autoconf \
    automake \
    libtool \
    gettext \
    intltool \
    2>/dev/null || true

# Clean dnf cache
dnf clean all
rm -rf /var/cache/dnf/*

# Remove temporary files
rm -rf /tmp/* /var/tmp/*

# Remove build scripts (they're baked in the image)
rm -rf /usr/libexec/woodpecker/*.py /usr/libexec/woodpecker/*.sh 2>/dev/null || true

# Remove repo configs (Pigeon repo not needed at runtime)
rm -f /etc/yum.repos.d/pigeon.repo

# Remove documentation
rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/*

# Remove locale data (keep only en_US)
localedef --list-archive | grep -v '^en_US' | xargs localedef --delete-from-archive 2>/dev/null || true
mv -f /usr/lib/locale/locale-archive /usr/lib/locale/locale-archive.tmpl 2>/dev/null || true
build-locale-archive 2>/dev/null || true

# Truncate logs
find /var/log -type f -exec truncate -s 0 {} \; 2>/dev/null || true

# Remove machine-id (regenerated on boot)
truncate -s 0 /etc/machine-id 2>/dev/null || true
truncate -s 0 /var/lib/dbus/machine-id 2>/dev/null || true

echo "Clean stage complete"