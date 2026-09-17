#!/usr/bin/env bash
# k0s first-boot setup
# Configures k0s to run Kubestellar + kubeflex + console on first boot
# This service runs once on first boot and then disables itself

set -euo pipefail

echo "Setting up k0s for Kubestellar..."

# Create k0s config directory
mkdir -p /etc/k0s

# Write k0s configuration with bundled manifests
cat > /etc/k0s/k0s.yaml << 'K0SCONFIG'
apiVersion: k0s.k0sproject.io/v1beta1
kind: ClusterConfig
metadata:
  name: woodpecker
spec:
  api:
    address: 0.0.0.0
    port: 6443
    sans:
      - "127.0.0.1"
      - "localhost"
      - "woodpecker"
  controllerManager: {}
  scheduler: {}
  network:
    provider: kube-router
    podCIDR: 10.244.0.0/16
    serviceCIDR: 10.96.0.0/12
    dualStack: false
    kubeProxy:
      mode: ipvs
  storage:
    type: etcd
    etcd:
      peerAddress: 127.0.0.1
      dataDir: /var/lib/etcd
  telemetry:
    enabled: false
  images:
    default_pull_policy: IfNotPresent
    konnectivity:
      image: ghcr.io/k0sproject/konnectivity-server:v0.0.36
  extensions:
    helm:
      enabled: true
      repositories:
        - name: kubestellar
          url: https://kubestellar.github.io/charts
    # Bundle manifests via bundle extension
    bundle:
      enabled: true
      manifests:
        - /var/lib/k0s/manifests
K0SCONFIG

# Create manifest directory
mkdir -p /var/lib/k0s/manifests

# Copy Kubestellar manifests
cp -r /usr/share/woodpecker/k0s/manifests/* /var/lib/k0s/manifests/ 2>/dev/null || true

# Enable k0s controller service
systemctl enable k0scontroller.service

# Mark first-boot as complete
touch /var/lib/woodpecker/k0s-first-boot.done

echo "k0s first-boot setup complete"