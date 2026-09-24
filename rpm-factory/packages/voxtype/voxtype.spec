# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/peteonrails/voxtype (tag v1.0.1).
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Offline-vendor mechanism: the build is hermetic, so crates.io deps travel
# as Source1. Regenerate on every version bump (maintainer, with network):
#   source_pipeline.py fetch voxtype --output /tmp/voxtype-src
#   tar -xzf /tmp/voxtype-src/v1.0.1.tar.gz && cd voxtype-1.0.1
#   cargo vendor --versioned-dirs vendor
#   tar -czf voxtype-1.0.1-vendor.tar.gz vendor/
# then record the vendor tarball digest alongside Source0.

%bcond_without check

Name:           voxtype
Version:        1.0.1
Release:        1.hum1.rpmfactory
Summary:        Push-to-talk voice-to-text for Linux
License:        MIT
URL:            https://github.com/peteonrails/voxtype
Source0:        https://github.com/peteonrails/voxtype/archive/refs/tags/v%{version}.tar.gz
# TODO(phase-2): generate + record vendor tarball, then uncomment:
# Source1:        voxtype-%{version}-vendor.tar.gz

BuildRequires:  cargo
BuildRequires:  rustc
BuildRequires:  gcc-c++
BuildRequires:  clang-devel
BuildRequires:  cmake
BuildRequires:  pkgconfig
BuildRequires:  pkgconfig(alsa)
BuildRequires:  systemd-rpm-macros
Requires:       curl
Requires:       pipewire-alsa
Recommends:     wtype
Recommends:     wl-clipboard
Suggests:       ydotool
Suggests:       libnotify

%description
Voxtype is a push-to-talk voice-to-text daemon for Linux.
Optimized for Wayland, works on X11 too. Hold a hotkey while speaking,
release to transcribe and output text at your cursor position.
Features:
- Fully offline transcription using whisper.cpp
- Native compositor keybinding support (Hyprland, Sway, River)
- Fallback chain: wtype (Wayland, CJK support), ydotool (X11), clipboard
- Configurable hotkeys, models, and output modes

This package includes tiered binaries:
- voxtype-avx2: CPU - Compatible with most CPUs from 2013+ (Intel Haswell, AMD Zen)
- voxtype-avx512: CPU - Optimized for newer CPUs (AMD Zen 4+, some Intel)
- voxtype-vulkan: GPU - Vulkan acceleration (NVIDIA, AMD, Intel)

The appropriate CPU binary is selected automatically at install time.
GPU acceleration can be enabled with: voxtype setup gpu --enable

%prep
%autosetup -n voxtype-%{version} -p1
# TODO(phase-2): unpack vendor tree and point cargo at it:
# tar -xzf %{SOURCE1}
# mkdir -p .cargo
# cat > .cargo/config.toml <<'EOF'
# [source.crates-io]
# replace-with = "vendored-sources"
# [source.vendored-sources]
# directory = "vendor"
# EOF

%build
export CARGO_HOME=%{_builddir}/cargo
# PIE is default for Rust binaries; ensure C/C++ code is compiled with -fPIE
# to match, otherwise linker fails with "recompile with -fPIE" errors.
export CFLAGS="%{build_cflags} -fPIE -pie"
export CXXFLAGS="%{build_cxxflags} -fPIE -pie"
export LDFLAGS="%{build_ldflags} -pie"

# Build AVX2 baseline binary (compatible with most CPUs from 2013+)
# Disable AVX-512 and GFNI in both Rust code and whisper.cpp to prevent
# SIGILL on older CPUs.
RUSTFLAGS="-C target-cpu=haswell -C target-feature=-avx512f,-avx512bw,-avx512cd,-avx512dq,-avx512vl,-gfni" \
GGML_NATIVE=OFF GGML_AVX512=OFF \
CMAKE_C_FLAGS="-mno-avx512f -mno-gfni -fPIE" CMAKE_CXX_FLAGS="-mno-avx512f -mno-gfni -fPIE" \
cargo build --release --locked
cp target/release/voxtype target/release/voxtype-avx2

# Build AVX-512 optimized binary (for Zen 4+, some Intel)
cargo clean
cargo build --release --locked
cp target/release/voxtype target/release/voxtype-avx512

# Build Vulkan GPU binary (for GPU acceleration)
cargo clean
RUSTFLAGS="-C target-cpu=haswell -C target-feature=-avx512f,-avx512bw,-avx512cd,-avx512dq,-avx512vl,-gfni" \
GGML_NATIVE=OFF GGML_AVX512=OFF \
CMAKE_C_FLAGS="-mno-avx512f -mno-gfni -fPIE" CMAKE_CXX_FLAGS="-mno-avx512f -mno-gfni -fPIE" \
cargo build --release --locked --features gpu-vulkan
cp target/release/voxtype target/release/voxtype-vulkan

%install
# Install tiered binaries to /usr/lib/voxtype/
install -D -m 755 target/release/voxtype-avx2 %{buildroot}%{_libdir}/voxtype/voxtype-avx2
install -D -m 755 target/release/voxtype-avx512 %{buildroot}%{_libdir}/voxtype/voxtype-avx512
install -D -m 755 target/release/voxtype-vulkan %{buildroot}%{_libdir}/voxtype/voxtype-vulkan

# Install default configuration
install -D -m 644 config/default.toml %{buildroot}%{_sysconfdir}/voxtype/config.toml

# Install systemd user service
install -D -m 644 packaging/systemd/voxtype.service \
    %{buildroot}%{_userunitdir}/voxtype.service

# Install documentation
install -D -m 644 README.md %{buildroot}%{_docdir}/%{name}/README.md
install -D -m 644 docs/INSTALL.md %{buildroot}%{_docdir}/%{name}/INSTALL.md

# Install license
install -D -m 644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

# Install shell completions
install -D -m 644 packaging/completions/voxtype.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/voxtype
install -D -m 644 packaging/completions/voxtype.zsh \
    %{buildroot}%{_datadir}/zsh/site-functions/_voxtype
install -D -m 644 packaging/completions/voxtype.fish \
    %{buildroot}%{_datadir}/fish/vendor_completions.d/voxtype.fish

# Install configuration TUI launcher (.desktop entry + terminal-picker script)
install -D -m 644 packaging/voxtype-configure.desktop \
    %{buildroot}%{_datadir}/applications/voxtype-configure.desktop
install -D -m 755 packaging/scripts/voxtype-configure-launcher \
    %{buildroot}%{_bindir}/voxtype-configure-launcher

%check
%if %{with check}
export CARGO_HOME=%{_builddir}/cargo
export CFLAGS="%{build_cflags} -fPIE -pie"
export CXXFLAGS="%{build_cxxflags} -fPIE -pie"
export LDFLAGS="%{build_ldflags} -pie"
# Only test with AVX2 build to avoid SIGILL in build environments
RUSTFLAGS="-C target-cpu=haswell -C target-feature=-avx512f,-avx512bw,-avx512cd,-avx512dq,-avx512vl,-gfni" \
GGML_NATIVE=OFF GGML_AVX512=OFF \
CMAKE_C_FLAGS="-mno-avx512f -mno-gfni -fPIE" CMAKE_CXX_FLAGS="-mno-avx512f -mno-gfni -fPIE" \
cargo test --release --locked
%endif

%post
%systemd_user_post voxtype.service

# Detect CPU capabilities and symlink the appropriate binary
rm -f %{_bindir}/voxtype

if [ -f /proc/cpuinfo ] && grep -q avx512f /proc/cpuinfo 2>/dev/null; then
    ln -sf %{_libdir}/voxtype/voxtype-avx512 %{_bindir}/voxtype
else
    ln -sf %{_libdir}/voxtype/voxtype-avx2 %{_bindir}/voxtype
fi

# Restore SELinux context if available
if command -v restorecon >/dev/null 2>&1; then
    restorecon %{_bindir}/voxtype 2>/dev/null || true
fi

# Detect GPU for Vulkan acceleration recommendation
GPU_DETECTED=""
if [ -d /dev/dri ] && ls /dev/dri/renderD* >/dev/null 2>&1; then
    if command -v lspci >/dev/null 2>&1; then
        GPU_INFO=$(lspci 2>/dev/null | grep -i 'vga\|3d\|display' | head -1 | sed 's/.*: //')
        [ -n "$GPU_INFO" ] && GPU_DETECTED="$GPU_INFO"
    fi
    [ -z "$GPU_DETECTED" ] && GPU_DETECTED="GPU detected (install pciutils for details)"
fi

if [ -n "$GPU_DETECTED" ]; then
    echo ""
    echo "GPU detected: $GPU_DETECTED"
    echo "  For GPU acceleration, run: sudo voxtype setup gpu --enable"
fi

echo ""
echo "=== Voxtype Post-Installation ==="
echo "  1. Add user to 'input' group: sudo usermod -aG input \$USER"
echo "  2. Download a model:  voxtype setup --download"
echo "  3. Start the daemon:   systemctl --user enable --now voxtype"

%preun
%systemd_user_preun voxtype.service

%postun
%systemd_user_postun_with_restart voxtype.service
# Remove symlink on package removal
rm -f %{_bindir}/voxtype

%files
%{_licensedir}/%{name}/LICENSE
%{_docdir}/%{name}/README.md
%{_docdir}/%{name}/INSTALL.md
%{_libdir}/voxtype/voxtype-avx2
%{_libdir}/voxtype/voxtype-avx512
%{_libdir}/voxtype/voxtype-vulkan
%ghost %{_bindir}/voxtype
%config(noreplace) %{_sysconfdir}/voxtype/config.toml
%{_userunitdir}/voxtype.service
%{_datadir}/bash-completion/completions/voxtype
%{_datadir}/zsh/site-functions/_voxtype
%{_datadir}/fish/vendor_completions.d/voxtype.fish
%{_datadir}/applications/voxtype-configure.desktop
%{_bindir}/voxtype-configure-launcher

%changelog
* Sat Sep 19 2026 Kestrel <kestrel@localhost> - 1.0.1-1.hum1.rpmfactory
- Initial Kestrel package (independent recipe, adapted from upstream dev spec)
