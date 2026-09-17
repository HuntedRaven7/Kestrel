#!/usr/bin/env bash
# Put the OGC (Optimized Generic Kernel) into this image.
# Hummingbird publishes no OGC RPM, so this is intentionally a source build.
#
# Compiling it takes ~30 min. The compile is hoisted into a cache image built
# from Containerfile.kernel and keyed by OGC tag+commit + base image digest.
# When that image is the base, the kernel arrives as a tarball and this script
# unpacks it. With no cache present -- a local build, or the cache image's
# own build -- it falls through to the source build, so both paths stay exercised.

set -euo pipefail

CACHE_DIR="${WARBLER_KERNEL_CACHE_DIR:-/warbler-cache}"
DNF="$(command -v dnf5 || command -v dnf)"

# Required kernel config options for gaming workloads
required_config=(SCHED_CLASS_EXT NTSYNC ANDROID_BINDERFS
    OVERLAY_FS SQUASHFS SQUASHFS_ZSTD EROFS_FS
    BLK_DEV_LOOP ISO9660_FS BLK_DEV_DM DM_SNAPSHOT DM_CRYPT
    CRYPTO_XTS FUSE_FS FS_VERITY)

verify_config() {
    local config="$1" symbol
    for symbol in "${required_config[@]}"; do
        if ! grep -Eq "^CONFIG_${symbol}=(y|m)$" "$config"; then
            echo "OGC kernel config $config is missing CONFIG_${symbol}" >&2
            return 1
        fi
    done
}

if [ -f "${CACHE_DIR}/ogc.tar" ]; then
    echo "Unpacking the prebuilt OGC kernel from ${CACHE_DIR}/ogc.tar"
    tar -C / -xf "${CACHE_DIR}/ogc.tar"

    release="$(cat /usr/lib/warbler/ogc-kernel-release)"

    # modules.dep may differ from base kernel; regenerate
    depmod -a "$release"
    ln -sfn "vmlinuz-${release}" /boot/vmlinuz

    test -s /usr/lib/warbler/ogc-kernel-release
    verify_config /usr/lib/warbler/ogc-kernel.config
    exit 0
fi

# OGC kernel pin: tag (what git can clone) + commit (what we verify)
# Update these when bumping OGC kernel version
OGC_TAG="${WARBLER_OGC_KERNEL_TAG:-v6.10.2-ogc1}"
OGC_COMMIT="${WARBLER_OGC_KERNEL_COMMIT:-TODO_OGC_COMMIT}"

builddir=/usr/src/warbler-ogc
toolchain=(bc bison cpio elfutils-libelf-devel flex gcc git make openssl-devel
    pahole perl python3 rsync xz zstd)

absent=()
for pkg in "${toolchain[@]}"; do
    rpm -q "$pkg" >/dev/null 2>&1 || absent+=("$pkg")
done

"$DNF" -y install "${toolchain[@]}"

git clone --depth 1 --branch "$OGC_TAG" https://github.com/OpenGamingCollective/linux.git "$builddir"

pushd "$builddir"
actual_commit="$(git rev-parse HEAD)"
if [ "$actual_commit" != "$OGC_COMMIT" ]; then
    echo "OGC tag $OGC_TAG resolves to $actual_commit, expected $OGC_COMMIT" >&2
    exit 1
fi

# Suppress "+" in version from shallow clone
export LOCALVERSION=

make defconfig

# Enable gaming-critical config options with dependencies
# SCHED_CLASS_EXT depends on BPF_SYSCALL && BPF_JIT && DEBUG_INFO_BTF
# DEBUG_INFO_BTF depends on BPF_SYSCALL, !DEBUG_INFO_REDUCED, pahole >= 1.22
# ANDROID_BINDERFS depends on ANDROID_BINDER_IPC
scripts/config --enable BPF_SYSCALL --enable BPF_JIT \
    --disable DEBUG_INFO_NONE \
    --enable DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT \
    --enable DEBUG_INFO_BTF \
    --enable SCHED_CLASS_EXT \
    --enable ANDROID_BINDER_IPC --enable ANDROID_BINDERFS \
    --enable NTSYNC

scripts/config --module OVERLAY_FS --module SQUASHFS --enable SQUASHFS_ZSTD \
    --module EROFS_FS --enable BLK_DEV_LOOP --enable ISO9660_FS \
    --enable BLK_DEV_DM --module DM_SNAPSHOT --module DM_CRYPT \
    --module CRYPTO_XTS --module FUSE_FS --enable FS_VERITY

scripts/config --set-str LOCALVERSION "-ogc1" --disable LOCALVERSION_AUTO

make olddefconfig

# Verify critical config immediately (before 30-min build)
require_config() {
    if ! grep -Eq "$1" .config; then
        echo "OGC kernel: olddefconfig dropped $2. Related settings:" >&2
        grep -E "^# ?CONFIG_(SCHED_CLASS_EXT|NTSYNC|ANDROID_BINDER|DEBUG_INFO|BPF_SYSCALL|BPF_JIT)" .config >&2 || true
        grep -E "^CONFIG_(SCHED_CLASS_EXT|NTSYNC|ANDROID_BINDER|DEBUG_INFO|BPF_SYSCALL|BPF_JIT)" .config >&2 || true
        exit 1
    fi
}

require_config '^CONFIG_SCHED_CLASS_EXT=y$' CONFIG_SCHED_CLASS_EXT
require_config '^CONFIG_NTSYNC=(y|m)$' CONFIG_NTSYNC
require_config '^CONFIG_ANDROID_BINDERFS=y$' CONFIG_ANDROID_BINDERFS

verify_config .config

make modules_prepare
make -j"$(nproc)" bzImage modules

release="$(make -s kernelrelease)"
make modules_install INSTALL_MOD_PATH=/usr INSTALL_MOD_STRIP=1

install -Dm0644 arch/x86/boot/bzImage "/boot/vmlinuz-${release}"
ln -sfn "vmlinuz-${release}" /boot/vmlinuz
install -Dm0644 .config "/usr/lib/modules/${release}/config"

# Preserve external-module build tree for NVIDIA module compilation
kernel_build="/usr/src/linux-${release}"
install -d "$kernel_build/arch"
cp -a Makefile Module.symvers .config include scripts "$kernel_build/"
cp -a arch/x86 "$kernel_build/arch/"

# objtool for external modules
if grep -qx "CONFIG_OBJTOOL=y" .config; then
    install -d "$kernel_build/tools/objtool"
    cp -a tools/objtool/. "$kernel_build/tools/objtool/"
fi

# Verify build tree completeness
for need in Makefile Module.symvers .config arch/x86/Makefile include scripts; do
    test -e "$kernel_build/$need" || {
        echo "OGC external-module build tree is missing $need" >&2
        find "$kernel_build" -maxdepth 2 >&2
        exit 1
    }
done

ln -sfn "$kernel_build" "/usr/lib/modules/${release}/build"
depmod -a "$release"

install -Dm0644 .config /usr/lib/warbler/ogc-kernel.config
printf '%s\n' "$release" >/usr/lib/warbler/ogc-kernel-release

popd
rm -rf "$builddir"

# Create cache archive if requested (cache image build)
if [ -n "${WARBLER_KERNEL_CACHE_OUT:-}" ]; then
    tar -C / -cf "${WARBLER_KERNEL_CACHE_OUT}" \
        "boot/vmlinuz-${release}" \
        "usr/lib/modules/${release}" \
        "usr/src/linux-${release}" \
        usr/lib/warbler/ogc-kernel.config \
        usr/lib/warbler/ogc-kernel-release
fi

# Remove toolchain packages we installed
if [ "${#absent[@]}" -gt 0 ]; then
    "$DNF" -y remove "${absent[@]}"
fi

"$DNF" clean all

# Final verification
test -s /usr/lib/warbler/ogc-kernel-release
verify_config /usr/lib/warbler/ogc-kernel.config