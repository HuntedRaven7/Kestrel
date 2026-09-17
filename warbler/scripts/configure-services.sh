#!/usr/bin/env bash
# Configure desktop services for Warbler
# Enables GDM, seatd, and sets up user services

set -euo pipefail

echo "Configuring system services..."

# Enable GDM
systemctl enable gdm.service

# Enable seatd (for wlroots compositors)
systemctl enable seatd.service

# Enable NetworkManager (if not already)
systemctl enable NetworkManager.service

# Enable bluetooth
systemctl enable bluetooth.service || true

# Enable cups
systemctl enable cups.service || true

# Enable flatpak system helper
systemctl enable flatpak-system-helper.service || true

# Set up bootc auto-update timer (disabled by default, user can enable)
# systemctl enable bootc-auto-update.timer || true

echo "Configuring user services (via global user dir)..."
# Create user service directory for default user services
mkdir -p /etc/systemd/user/default.target.wants

# Note: quickshell.service and awww.service are user services
# They are started by Mango autostart, not enabled globally

echo "Setting up GDM autologin (opt-in)..."
# GDM autologin is configured via drop-in at /etc/gdm/custom.conf.d/10-warbler-autologin.conf
# The drop-in is copied via COPY system_files/shared/ in Containerfile
# It's commented by default - user must uncomment and set username at install time

echo "Configuring login defaults..."
# Ensure wayland is enabled
mkdir -p /etc/gdm/custom.conf.d
if [ ! -f /etc/gdm/custom.conf.d/10-warbler-autologin.conf ]; then
    cat > /etc/gdm/custom.conf.d/10-warbler-autologin.conf << 'EOF'
[daemon]
# Opt-in kiosk autologin. The login user is created at install time;
# never bake in a known password (see AGENTS.md safety).
# Uncomment and set username to enable:
# AutomaticLoginEnable=true
# AutomaticLogin=kestrel
WaylandEnable=true
EOF
fi

echo "Service configuration complete"