#!/usr/bin/env bash
# Configure branding for Woodpecker image
# Sets os-release, hostname, etc.

set -euo pipefail

echo "Configuring branding..."

# Read version from build arg or default
VERSION="${VERSION:-testing}"
IMAGE_NAME="${IMAGE_NAME:-woodpecker}"

# Write /etc/os-release
cat > /etc/os-release << EOF
NAME="Woodpecker"
VERSION="${VERSION}"
ID=woodpecker
ID_LIKE="fedora hummingbird"
VERSION_ID="${VERSION}"
PRETTY_NAME="Woodpecker ${VERSION}"
ANSI_COLOR="0;32"
HOME_URL="https://github.com/HuntedRaven7/Kestrel"
SUPPORT_URL="https://github.com/HuntedRaven7/Kestrel/issues"
BUG_REPORT_URL="https://github.com/HuntedRaven7/Kestrel/issues"
VARIANT="server"
VARIANT_ID="server"
EOF

# Write /etc/hostname
echo "woodpecker" > /etc/hostname

# Write /etc/machine-info
cat > /etc/machine-info << EOF
PRETTY_HOSTNAME="Woodpecker"
ICON_NAME=computer-server
CHASSIS=server
DEPLOYMENT=production
EOF

# Set up motd
cat > /etc/motd << EOF

Woodpecker ${VERSION}
Hummingbird-based server
https://github.com/HuntedRaven7/Kestrel

EOF

# Ensure /etc/os-release is a symlink to /usr/lib/os-release for bootc
ln -sf /etc/os-release /usr/lib/os-release

echo "Branding configured: ${IMAGE_NAME} ${VERSION}"