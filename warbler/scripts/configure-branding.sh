#!/usr/bin/env bash
# Configure branding for Warbler image
# Sets os-release, hostname, etc.

set -euo pipefail

echo "Configuring branding..."

# Read version from build arg or default
VERSION="${VERSION:-testing}"
IMAGE_NAME="${IMAGE_NAME:-warbler}"
IMAGE_FLAVOR="${IMAGE_FLAVOR:-main}"

# Write /etc/os-release
cat > /etc/os-release << EOF
NAME="Warbler"
VERSION="${VERSION} (${IMAGE_FLAVOR})"
ID=warbler
ID_LIKE="fedora hummingbird"
VERSION_ID="${VERSION}"
PRETTY_NAME="Warbler ${VERSION} (${IMAGE_FLAVOR})"
ANSI_COLOR="0;34"
HOME_URL="https://github.com/HuntedRaven7/Kestrel"
SUPPORT_URL="https://github.com/HuntedRaven7/Kestrel/issues"
BUG_REPORT_URL="https://github.com/HuntedRaven7/Kestrel/issues"
VARIANT="${IMAGE_FLAVOR}"
VARIANT_ID="${IMAGE_FLAVOR}"
EOF

# Write /etc/hostname
echo "warbler" > /etc/hostname

# Write /etc/machine-info
cat > /etc/machine-info << EOF
PRETTY_HOSTNAME="Warbler"
ICON_NAME=computer-laptop
CHASSIS=laptop
DEPLOYMENT=production
EOF

# Set up motd
cat > /etc/motd << EOF

Warbler ${VERSION} (${IMAGE_FLAVOR})
Hummingbird-based Mango desktop
https://github.com/HuntedRaven7/Kestrel

EOF

# Ensure /etc/os-release is a symlink to /usr/lib/os-release for bootc
ln -sf /etc/os-release /usr/lib/os-release

echo "Branding configured: ${IMAGE_NAME} ${VERSION} (${IMAGE_FLAVOR})"