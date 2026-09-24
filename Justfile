# Kestrel Justfile — run `just --list` before inventing maintenance commands.

check:
    python3 rpm-factory/tools/factory_contract.py
    python3 rpm-factory/tools/validate.py
    python3 rpm-factory/tools/sync_versions.py --check
    python3 rpm-factory/tools/audit_sources.py --spec-sources

sync-versions:
    python3 rpm-factory/tools/sync_versions.py

test:
    python3 -m pytest rpm-factory/tests -q

tine-generate:
    tine/bin/tine buck run tine//tools:dev.box -- python3 rpm-factory/tools/tine_metadata.py --write

tine-check:
    tine/bin/tine buck run tine//tools:dev.box -- python3 rpm-factory/tools/tine_metadata.py --check

tine-build pkg:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 rpm-factory/tools/stage_sources.py "{{ pkg }}"
    rm -rf "work/tine-local/{{ pkg }}"
    tine/bin/tine buck build "//rpm-factory:{{ pkg }}" --out "work/tine-local/{{ pkg }}"
    find "work/tine-local/{{ pkg }}" -type f -name '*.rpm' -print

build-rpm-factory:
    # Full builds run in the chunked GitHub workflow; locally build selected packages with `just tine-build <pkg>`.
    @echo "Use `just tine-build <pkg>` locally or run rebuild-rpm-factory.yml for all chunks."

build-warbler flavor="main":
    podman build -f warbler/Containerfile \
      --build-arg BASE_IMAGE=quay.io/hummingbird-community/bootc-os@sha256:TODO_BASE_IMAGE_SHA \
      --build-arg RPM_FACTORY_IMAGE=ghcr.io/huntedraven7/rpm-factory \
      --build-arg RPM_FACTORY_IMAGE_SHA=sha256:TODO_RPM_FACTORY_IMAGE_SHA \
      --build-arg IMAGE_FLAVOR={{ flavor }} \
      --build-arg VERSION=local \
      -t ghcr.io/huntedraven7/warbler:{{ flavor }}-local \
      warbler/.

build-woodpecker:
    podman build -f woodpecker/Containerfile \
      --build-arg BASE_IMAGE=quay.io/hummingbird-community/bootc-os@sha256:TODO_BASE_IMAGE_SHA \
      --build-arg RPM_FACTORY_IMAGE=ghcr.io/huntedraven7/rpm-factory \
      --build-arg RPM_FACTORY_IMAGE_SHA=sha256:TODO_RPM_FACTORY_IMAGE_SHA \
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
    echo "TODO: import Fedora dist-git rawhide branch for {{ pkg }} into rpm-factory/packages/{{ pkg }}/ (PR, with .hummingbird-upstream.json)"

srpm pkg:
    just tine-build {{ pkg }}
    @echo "Tine emits the source RPM alongside the binary RPMs in work/tine-local/{{ pkg }}"

bump-check:
    echo "TODO: report Renovate open bump PRs"

sync-bluefin-toml:
    curl -fsSL https://raw.githubusercontent.com/projectbluefin/bluefin-cli/main/base.toml -o warbler/packages/bluefin.toml
    echo "Synced bluefin.toml - verify no drift with CI"
