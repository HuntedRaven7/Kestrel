#!/usr/bin/env bash
# Configure server services for Woodpecker
# Enables cockpit, uupd, bootc-auto-update, ssh (disabled by default), tailscale, etc.

set -euo pipefail

echo "Configuring system services..."

# Enable cockpit
systemctl enable cockpit.socket

# Enable uupd (update daemon)
systemctl enable uupd.timer || true

# Enable bootc-auto-update timer
systemctl enable bootc-auto-update.timer || true

# Enable NetworkManager
systemctl enable NetworkManager.service

# Enable firewalld
systemctl enable firewalld.service

# Enable chrony (NTP)
systemctl enable chronyd.service

# SSH: disabled by default (ENABLE_SSHD=0)
# User must explicitly enable: systemctl enable --now sshd.socket
# We install the socket but don't enable it
systemctl disable sshd.socket 2>/dev/null || true

# Tailscale: disabled by default (opt-in)
systemctl disable tailscaled.service 2>/dev/null || true

# WireGuard: disabled by default (opt-in)
systemctl disable wg-quick@wg0.service 2>/dev/null || true

# Enable podman socket (rootless)
systemctl --global enable podman.socket || true

# Enable k0s first-boot service (sets up Kubestellar on first boot)
systemctl enable k0s-first-boot.service

# Set up SSH config (hardened defaults)
mkdir -p /etc/ssh
cat > /etc/ssh/sshd_config.d/99-woodpecker-hardening.conf << 'EOF'
# Woodpecker SSH hardening
# See contracts/server.toml for contract values

# Authentication
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Crypto
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512

# Security
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PermitTunnel no
DebianBanner no
Banner /etc/ssh/banner

# Logging
SyslogFacility AUTH
LogLevel VERBOSE

# Limits
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

# Create SSH banner
cat > /etc/ssh/banner << 'EOF'
***************************************************************************
*                    AUTHORIZED ACCESS ONLY                               *
*                                                                         *
* This system is for authorized users only. All activities are monitored  *
* and logged. Unauthorized access will be prosecuted.                     *
***************************************************************************
EOF

# Configure firewalld (allow cockpit, ssh if enabled)
firewall-offline-cmd --add-service=cockpit --permanent || true
firewall-offline-cmd --add-service=ssh --permanent || true

# k0s API server
firewall-offline-cmd --add-port=6443/tcp --permanent || true

# Kubestellar console
firewall-offline-cmd --add-port=8080/tcp --permanent || true

# Configure cockpit
mkdir -p /etc/cockpit
cat > /etc/cockpit/cockpit.conf << 'EOF'
[WebService]
Origins = https://localhost:9090 https://127.0.0.1:9090
AllowUnencrypted = false
MaxStartups = 10
IdleTimeout = 300

[Session]
Timeout = 900
EOF

echo "Service configuration complete"