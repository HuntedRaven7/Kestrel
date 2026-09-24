# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://codeberg.org/LGFae/awww (archive v0.12.1), GPL-3.0.
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Offline-vendor mechanism: the build is hermetic, so crates.io deps travel
# as the digest-locked Source1 archive. Regenerate it on every version bump
# (maintainer, with network), then update its SHA-512 in upstream-sources.json.

Name:           awww
Version:        0.12.1
Release:        1.hum1.rpmfactory
Summary:        Wayland wallpaper daemon (client + daemon)
# Cargo vendor sources contain Rust attributes such as #![no_std] at the
# beginning of files. The RPM shebang mangler mistakes those attributes for
# scripts, so leave this buildroot check disabled for this Rust-only package.
%global __brp_mangle_shebangs %{nil}
License:        GPL-3.0-only
URL:            https://codeberg.org/LGFae/awww
Source0:        https://codeberg.org/LGFae/awww/archive/v%{version}.tar.gz
Source1:        %{name}-%{version}-vendor.tar.gz

BuildRequires:  cargo
BuildRequires:  rustc
BuildRequires:  gcc
# common/build.rs probes liblz4 >= 1.8 via pkg-config
BuildRequires:  pkgconfig(liblz4)
# dav1d-sys crate needs dav1d library
BuildRequires:  libdav1d-devel
# waybackend-scanner crate needs wayland-protocols
# and uses pkg-config to find wayland.xml from wayland-client/wayland-scanner
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(wayland-protocols)

%description
awww: animated wallpaper daemon for Wayland (here: Mango). Binaries:
awww (client) and awww-daemon. The systemd user unit ships in the
Warbler image layer (warbler/system_files), not in this RPM.

%prep
%autosetup -n awww -p1
tar -xzf %{SOURCE1}
mkdir -p .cargo
cat > .cargo/config.toml <<'EOF'
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
EOF

%build
cargo build --release --workspace --all-features --locked --offline

%install
install -Dm0755 target/release/awww %{buildroot}%{_bindir}/awww
install -Dm0755 target/release/awww-daemon %{buildroot}%{_bindir}/awww-daemon

%files
%license LICENSE
%{_bindir}/awww
%{_bindir}/awww-daemon
%doc README.md CHANGELOG.md

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.12.1-1.hum1.rpmfactory
- Initial Kestrel package (independent recipe)
- Add a digest-locked Cargo vendor archive for hermetic builds
