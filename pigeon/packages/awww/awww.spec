# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://codeberg.org/LGFae/awww (archive v0.12.1), GPL-3.0.
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Offline-vendor mechanism: the build is hermetic, so crates.io deps travel
# as Source1. Regenerate on every version bump (maintainer, with network):
#   source_pipeline.py fetch awww --output /tmp/awww-src
#   tar -xzf /tmp/awww-src/v0.12.1.tar.gz && cd awww
#   cargo vendor --versioned-dirs vendor
#   tar -czf awww-0.12.1-vendor.tar.gz vendor/
# then record the vendor tarball digest alongside Source0.

Name:           awww
Version:        0.12.1
Release:        1.hum1.pigeon
Summary:        Wayland wallpaper daemon (client + daemon)
License:        GPL-3.0-only
URL:            https://codeberg.org/LGFae/awww
Source0:        https://codeberg.org/LGFae/awww/archive/v%{version}.tar.gz
# TODO(phase-2): generate + record vendor tarball, then uncomment:
# Source1:        %{name}-%{version}-vendor.tar.gz

BuildRequires:  cargo
BuildRequires:  rustc
BuildRequires:  gcc
# common/build.rs probes liblz4 >= 1.8 via pkg-config
BuildRequires:  pkgconfig(liblz4)
# dav1d-sys crate needs dav1d library
BuildRequires:  libdav1d-devel

%description
awww: animated wallpaper daemon for Wayland (here: Mango). Binaries:
awww (client) and awww-daemon. The systemd user unit ships in the
Warbler image layer (warbler/system_files), not in this RPM.

%prep
%autosetup -n awww -p1
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
# TODO(phase-2): add --offline once Source1 vendor tree lands
cargo build --release --workspace --all-features

%install
install -Dm0755 target/release/awww %{buildroot}%{_bindir}/awww
install -Dm0755 target/release/awww-daemon %{buildroot}%{_bindir}/awww-daemon

%files
%license LICENSE
%{_bindir}/awww
%{_bindir}/awww-daemon
%doc README.md CHANGELOG.md

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.12.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe; vendor tree pending)
