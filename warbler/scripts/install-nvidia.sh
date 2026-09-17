#!/usr/bin/env bash
# Build NVIDIA's open kernel module from source against the kernel this image runs.
#
# No prebuilt module exists for Hummingbird's kernel (UBlue's akmods bundle
# doesn't cover Hummingbird). NVIDIA's .run installer is the only source.
#
# Both driver download and module compile are hoisted into the cache image
# (Containerfile.kernel). The userspace install runs the .run installer over
# a populated /usr and must happen after package transaction, so it's not cached.

set -euo pipefail

flavor="${1:-main}"

DNF="$(command -v dnf5 || command -v dnf)"
CACHE_DIR="${WARBLER_KERNEL_CACHE_DIR:-/warbler-cache}"

# Cache-only mode: compile modules, archive them, skip userspace install
modules_only="${WARBLER_NVIDIA_MODULES_ONLY:-}"

# NVIDIA driver version (from https://download.nvidia.com/XFree86/Linux-x86_64/latest.txt)
driver_version="${WARBLER_NVIDIA_DRIVER_VERSION:-595.84}"
run="NVIDIA-Linux-x86_64-${driver_version}.run"
url="https://download.nvidia.com/XFree86/Linux-x86_64/${driver_version}/${run}"
sha_url="${url}.sha256sum"

# OGC kernel release (if installed)
ogc_release=""
[ -f /usr/lib/warbler/ogc-kernel-release ] && ogc_release="$(cat /usr/lib/warbler/ogc-kernel-release)"

# Identify base kernel from module trees (exclude OGC kernel)
kernel="$(for d in /usr/lib/modules/*/; do
    d="${d%/}"; d="${d##*/}"
    [ "$d" = "$ogc_release" ] || echo "$d"
done | sort -V | tail -n1)"

diagnose() {
    echo "--- /usr/lib/modules" >&2; ls -1 /usr/lib/modules >&2 || true
    echo "--- installed kernel packages" >&2; rpm -qa "kernel*" | sort >&2 || true
    echo "--- ogc release: ${ogc_release:-none}, base kernel: ${kernel:-none}" >&2
}

if [ -z "$kernel" ]; then
    echo "No base kernel module tree found; cannot build NVIDIA module" >&2
    diagnose
    exit 1
fi

# Kernel-devel from Koji (base kernel is pinned by BASE_IMAGE digest)
# Update KERNEL_DEVEL_SHA256 when base image changes
KERNEL_DEVEL_SHA256="${WARBLER_KERNEL_DEVEL_SHA256:-TODO_KERNEL_DEVEL_SHA256}"
build_tree="/usr/lib/modules/${kernel}/build"
installed_kernel_devel=""

nvidia_toolchain=(gcc make kmod)
nvidia_absent=()
toolchain_ready=""

ensure_toolchain() {
    [ -n "$toolchain_ready" ] && return 0
    toolchain_ready=1

    if [ ! -d "$build_tree" ]; then
        echo "No build tree at $build_tree; supplying kernel-devel-${kernel}"
        if "$DNF" -y install "kernel-devel-${kernel}"; then
            installed_kernel_devel="kernel-devel-${kernel}"
        else
            local arch nv ver rel koji rpmfile actual
            arch="${kernel##*.}"; nv="${kernel%.*}"; ver="${nv%%-*}"; rel="${nv#*-}"
            koji="https://kojipkgs.fedoraproject.org/packages/kernel/${ver}/${rel}/${arch}"
            rpmfile="kernel-devel-${ver}-${rel}.${arch}.rpm"
            echo "Not in enabled repositories; taking from ${koji}/${rpmfile}"
            curl --retry 3 --retry-all-errors -fsSLo "/tmp/${rpmfile}" "${koji}/${rpmfile}"
            actual="$(sha256sum "/tmp/${rpmfile}" | cut -d' ' -f1)"
            if [ "$actual" != "$KERNEL_DEVEL_SHA256" ]; then
                echo "kernel-devel SHA-256 is $actual, expected $KERNEL_DEVEL_SHA256" >&2
                echo "Base image kernel has moved; update KERNEL_DEVEL_SHA256." >&2
                exit 1
            fi
            "$DNF" -y install "/tmp/${rpmfile}"
            installed_kernel_devel="kernel-devel"
            rm -f "/tmp/${rpmfile}"
        fi
    fi

    if [ ! -d "$build_tree" ]; then
        echo "Still no kernel build tree at $build_tree after installing kernel-devel" >&2
        diagnose
        exit 1
    fi

    local pkg
    for pkg in "${nvidia_toolchain[@]}"; do
        rpm -q "$pkg" >/dev/null 2>&1 || nvidia_absent+=("$pkg")
    done
    "$DNF" -y install "${nvidia_toolchain[@]}"
}

# Get installer (from cache or download + verify)
if [ -f "${CACHE_DIR}/nvidia-installer.run" ]; then
    run_path="${CACHE_DIR}/nvidia-installer.run"
else
    run_path="/tmp/${run}"
    curl --retry 3 --retry-all-errors -fsSLo "$run_path" "$url"

    # Verify against NVIDIA's published SHA-256
    expected="$(curl --retry 3 --retry-all-errors -fsSL "$sha_url" | awk 'NR==1{print $1}')"
    if [ -z "$expected" ]; then
        echo "Could not fetch NVIDIA installer SHA-256 from ${sha_url}" >&2
        exit 1
    fi
    actual="$(sha256sum "$run_path" | cut -d' ' -f1)"
    if [ "$actual" != "$expected" ]; then
        echo "NVIDIA installer SHA-256 is $actual, expected $expected" >&2
        exit 1
    fi
fi

ensure_source() {
    [ -d /tmp/nvidia-source ] || sh "$run_path" --extract-only --target /tmp/nvidia-source
}

provided=()

build_module() {
    local release="$1"
    local tree="/usr/lib/modules/$1/build"
    local cached="${CACHE_DIR}/nvidia-modules-${release}.tar"

    if [ -f "$cached" ]; then
        echo "Unpacking prebuilt NVIDIA module for ${release}"
        tar -C / -xf "$cached"
    else
        ensure_toolchain
        test -d "$tree"
        ensure_source

        # Use NVIDIA's Makefile (not kernel Kbuild directly)
        make -j"$(nproc)" -C /tmp/nvidia-source/kernel-open modules SYSSRC="$tree"

        install -d "/usr/lib/modules/${release}/extra/nvidia"
        find /tmp/nvidia-source/kernel-open -name 'nvidia*.ko' \
            -exec install -m0644 -t "/usr/lib/modules/${release}/extra/nvidia" {} +

        make -C /tmp/nvidia-source/kernel-open clean SYSSRC="$tree"
    fi

    # Assert module landed
    if [ ! -f "/usr/lib/modules/${release}/extra/nvidia/nvidia.ko" ]; then
        echo "No nvidia.ko for ${release} after providing module" >&2
        echo "--- /usr/lib/modules/${release}/extra" >&2
        find "/usr/lib/modules/${release}/extra" -maxdepth 3 >&2 2>/dev/null || echo "(absent)" >&2
        if [ -f "$cached" ]; then
            echo "--- contents of ${cached}" >&2
            tar -tf "$cached" >&2 || true
        fi
        exit 1
    fi

    depmod -a "$release"
    provided+=("$release")

    if [ -n "${WARBLER_KERNEL_CACHE_OUT_DIR:-}" ]; then
        tar -C / -cf "${WARBLER_KERNEL_CACHE_OUT_DIR}/nvidia-modules-${release}.tar" \
            "usr/lib/modules/${release}/extra/nvidia"
    fi
}

build_module "$kernel"

if [ -n "$modules_only" ]; then
    if [[ "$flavor" == *gaming ]]; then
        build_module "${ogc_release:?}"
    fi
    cp -f "$run_path" "${WARBLER_KERNEL_CACHE_OUT_DIR:?}/nvidia-installer.run"
    rm -rf /tmp/nvidia-source
    exit 0
fi

# Userspace install (runs after package transaction)
sh "$run_path" --silent --no-kernel-module --no-nouveau-check \
    --no-rebuild-initramfs --no-backup --install-libglvnd

# nvidia-container-toolkit
"$DNF" -y install nvidia-container-toolkit

# Kernel args and modprobe blacklist
install -d /usr/lib/bootc/kargs.d /usr/lib/modprobe.d /usr/lib/warbler
printf '%s\n' 'blacklist nouveau' 'options nouveau modeset=0' >/usr/lib/modprobe.d/00-nouveau-blacklist.conf
printf '%s\n' 'kargs = ["rd.driver.blacklist=nouveau", "modprobe.blacklist=nouveau", "nvidia-drm.modeset=1"]' >/usr/lib/bootc/kargs.d/00-nvidia.toml
printf '%s\n' "$driver_version" >/usr/lib/warbler/nvidia-driver-version

if [[ "$flavor" == nvidia-gaming ]]; then
    build_module "${ogc_release:?}"
fi

rm -rf "/tmp/${run}" /tmp/nvidia-source

# Remove toolchain + kernel-devel we installed
nvidia_drop=("${nvidia_absent[@]}")
if [ -n "$installed_kernel_devel" ]; then
    nvidia_drop+=("$installed_kernel_devel")
fi
if [ "${#nvidia_drop[@]}" -gt 0 ]; then
    "$DNF" -y remove "${nvidia_drop[@]}"
fi
"$DNF" clean all

# Verify modules survived the userspace install + removal
for release in "${provided[@]}"; do
    if [ ! -f "/usr/lib/modules/${release}/extra/nvidia/nvidia.ko" ]; then
        echo "nvidia.ko for ${release} was present when built and is gone now" >&2
        find "/usr/lib/modules/${release}" -maxdepth 2 >&2 2>/dev/null || echo "(tree absent)" >&2
        exit 1
    fi
done