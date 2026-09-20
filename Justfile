# Kestrel Justfile — run `just --list` before inventing commands.

check:
    python3 pigeon/tools/factory_contract.py
    python3 pigeon/tools/validate.py
    python3 pigeon/tools/sync_versions.py --check

sync-versions:
    python3 pigeon/tools/sync_versions.py

test:
    python3 -m pytest pigeon/tests -q

build-pigeon:
    echo "TODO(phase-2): local pigeon stage build (podman + fedora:44 container)"

build-warbler flavor="main":
    podman build -f warbler/Containerfile \
      --build-arg BASE_IMAGE=quay.io/hummingbird-community/bootc-os@sha256:TODO_BASE_IMAGE_SHA \
      --build-arg PIGEON_IMAGE=ghcr.io/huntedraven7/pigeon@sha256:TODO_PIGEON_IMAGE_SHA \
      --build-arg IMAGE_FLAVOR={{ flavor }} \
      --build-arg VERSION=local \
      -t ghcr.io/huntedraven7/warbler:{{ flavor }}-local \
      warbler/.

build-woodpecker:
    podman build -f woodpecker/Containerfile \
      --build-arg BASE_IMAGE=quay.io/hummingbird-community/bootc-os@sha256:TODO_BASE_IMAGE_SHA \
      --build-arg PIGEON_IMAGE=ghcr.io/huntedraven7/pigeon@sha256:TODO_PIGEON_IMAGE_SHA \
      --build-arg VERSION=local \
      -t ghcr.io/huntedraven7/woodpecker:local \
      woodpecker/.

iso image="warbler" flavor="main":
    podman pull quay.io/centos-bootc/bootc-image-builder:latest
    if [ "{{ image }}" = "warbler" ]; then \
      podman pull ghcr.io/huntedraven7/warbler:{{ flavor }}-local; \
      IMAGE_REF="ghcr.io/huntedraven7/warbler:{{ flavor }}-local"; \
      ISO_NAME="warbler-{{ flavor }}-local"; \
    else \
      podman pull ghcr.io/huntedraven7/woodpecker:local; \
      IMAGE_REF="ghcr.io/huntedraven7/woodpecker:local"; \
      ISO_NAME="woodpecker-local"; \
    fi
    mkdir -p iso-output
    podman run --rm --privileged \
      -v /var/lib/containers:/var/lib/containers \
      -v $(pwd)/iso-output:/output \
      quay.io/centos-bootc/bootc-image-builder:latest \
      --type iso \
      --output-dir /output \
      ${IMAGE_REF}
    ls -la iso-output/

qemu-boot image="warbler:main" disk-size="20G" memory="4G":
    # Boot the image in QEMU with KVM
    # Usage: just qemu-boot image=ghcr.io/huntedraven7/warbler:main-testing
    podman run --rm --privileged \
      -v /var/lib/containers:/var/lib/containers \
      {{ image }} \
      bootc install to-existing-root --acknowledge-destructive /dev/null 2>&1 | head -20 || true
    # For actual QEMU boot, use:
    # qemu-system-x86_64 -enable-kvm -m {{ memory }} -drive file=disk.qcow2,format=qcow2 -net nic,model=virtio -net user

qemu-boot-iso iso-path="iso-output/warbler-main-local.iso" memory="4G":
    # Boot ISO in QEMU
    qemu-system-x86_64 -enable-kvm -m {{ memory }} -cdrom {{ iso-path }} -boot d

import pkg:
    echo "TODO: import Fedora dist-git rawhide branch for {{ pkg }} into pigeon/packages/{{ pkg }}/ (PR, with .hummingbird-upstream.json)"

srpm pkg:
    #!/usr/bin/env bash
    # Local SRPM build mirroring the rebuild-pigeon SRPM wave
    # (stage-sources + rpmbuild -bs). Requires rpm-build on the host.
    set -euo pipefail
    mkdir -p work/srpm
    PKG="{{ pkg }}"
    if python3 -c "import json,sys; sys.exit(0 if json.load(open('pigeon/config/upstream-sources.json'))['packages']['$PKG'].get('vendored') else 1)"; then \
      python3 pigeon/tools/fetch_vendored.py --package "$PKG"; \
    fi
    python3 pigeon/tools/audit_sources.py --fix --package "$PKG"
    python3 pigeon/tools/source_pipeline.py fetch "$PKG" \
      --output work/srpm --stage-into pigeon/packages
    SPEC=$(ls pigeon/packages/"$PKG"/*.spec | head -1)
    rpmbuild -bs "$SPEC" \
      --define "_sourcedir $PWD/pigeon/packages/$PKG" \
      --define "_srcrpmdir $PWD/work/srpm"
    ls work/srpm/*.src.rpm

bump-check:
    echo "TODO: report Renovate open bump PRs"

sync-bluefin-toml:
    curl -fsSL https://raw.githubusercontent.com/projectbluefin/bluefin-cli/main/base.toml -o warbler/packages/bluefin.toml
    echo "Synced bluefin.toml - verify no drift with CI"