---
name: sddm-autologin
description: SDDM autologin into Mango, session files, login policy
---
# SDDM autologin

Drop-in: `etc/sddm.conf.d/10-warbler-autologin.conf` (opt-in kiosk).
Session file comes from the mango RPM (`usr/share/wayland-sessions/mango.desktop`).
Theme stays at SDDM's built-in `maldives` (no breeze/plasma dep).
Never bake in a known password; user created at install time.
