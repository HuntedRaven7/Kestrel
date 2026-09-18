#!/usr/bin/env bash
# Configure desktop services for Warbler
# Enables SDDM, seatd, and sets up user services

set -euo pipefail

echo "Configuring system services..."

# Enable SDDM (display manager; autologins into the Mango session)
systemctl enable sddm.service

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

echo "Setting up SDDM autologin (opt-in)..."
# SDDM autologin lives in /etc/sddm.conf.d/10-warbler-autologin.conf
# (shipped under system_files/shared/). It is inert until a username is
# set: the login user is created at install time, never baked in.

echo "Configuring login defaults..."
# Mango session file comes from the mango RPM
# (/usr/share/wayland-sessions/mango.desktop); SDDM picks it up by name
# via Session=mango.desktop. Theme stays at SDDM's built-in maldives
# (no breeze/plasma dependency).

echo "Service configuration complete"
