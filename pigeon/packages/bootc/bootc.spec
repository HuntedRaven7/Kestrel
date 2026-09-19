# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/bootc-dev/bootc (tag v1.16.10).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%bcond_without check
%bcond_with tests
%if 0%{?rhel} >= 9 || 0%{?fedora} > 41
    %bcond_without ostree_ext
%else
    %bcond_with ostree_ext
%endif

%if 0%{?rhel}
    %bcond_without rhsm
%else
    %bcond_with rhsm
%endif

%global rust_minor %(rustc --version | cut -f2 -d" " | cut -f2 -d".")

%if 0%{?fedora} || 0%{?rhel} >= 10 || 0%{?rust_minor} >= 89
    %global new_cargo_macros 1
%else
    %global new_cargo_macros 0
%endif

Name:           bootc
Version:        1.16.10
Release:        1.hum1.pigeon
Summary:        Bootable container system

License:        Apache-2.0 AND BSD-3-Clause AND MIT AND (Apache-2.0 OR BSL-1.0) AND (Apache-2.0 OR MIT) AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) AND (Unlicense OR MIT)
URL:            https://github.com/bootc-dev/bootc
Source0:        https://github.com/bootc-dev/bootc/releases/download/v%{version}/bootc-%{version}.tar.zstd
Source1:        https://github.com/bootc-dev/bootc/releases/download/v%{version}/bootc-%{version}-vendor.tar.zstd

ExcludeArch:    %{ix86}

BuildRequires: libzstd-devel
BuildRequires: make
BuildRequires: ostree-devel
BuildRequires: openssl-devel
BuildRequires: go-md2man
%if 0%{?rhel}
BuildRequires: rust-toolset
%else
BuildRequires: cargo-rpm-macros >= 25
%endif
BuildRequires: systemd
BuildRequires: cargo
BuildRequires: rustc

Requires: composefs
Requires: ostree
Requires: skopeo
Requires: podman
Requires: util-linux-core
Requires: /usr/bin/chcon
Recommends: bootupd

Provides: ostree-cli(ostree-container)

%description
Bootable container system.

%package -n system-reinstall-bootc
Summary: Utility to reinstall the current system using bootc
Recommends: podman

%description -n system-reinstall-bootc
This package provides a utility to simplify reinstalling the current system to a given bootc image.

%prep
%autosetup -n bootc-1.16.10
# Unpack vendor tree for hermetic offline build
tar --zstd -xf %{SOURCE1}
# Default -v vendor config doesn't support non-crates.io deps (i.e. git)
cp .cargo/vendor-config.toml .
%cargo_prep -N
cat vendor-config.toml >> .cargo/config.toml
rm vendor-config.toml

%build
%cargo_build

%install
%cargo_install

%files
%license LICENSE
%{_bindir}/bootc
%{_bindir}/system-reinstall-bootc
%{_mandir}/man1/bootc.1*
%{_mandir}/man1/system-reinstall-bootc.1*
%{_unitdir}/bootc-fetch-updates.service
%{_unitdir}/bootc-fetch-updates.timer
%{_datadir}/bash-completion/completions/bootc

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.16.10-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
- Use vendor-config.toml for git dependencies (composefs-ctl)