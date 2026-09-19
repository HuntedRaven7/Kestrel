# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream mirror: https://github.com/quickshell-mirror/quickshell (tag v0.3.1,
# GPG-signed 1a4716c). Canonical upstream: https://git.outfoxxed.me/quickshell/quickshell
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
# CAUTION: Quickshell uses private Qt APIs — rebuild on EVERY Qt update
# (Renovate group qt-quickshell couples them).

Name:           quickshell
Version:        0.3.1
Release:        1.hum1.pigeon
Summary:        Flexible toolkit for desktop shells with QtQuick
License:        LGPL-3.0-only
URL:            https://quickshell.org
Source0:        https://github.com/quickshell-mirror/quickshell/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  pkgconfig
BuildRequires:  cli11-devel
BuildRequires:  cpptrace-devel
BuildRequires:  jemalloc-devel
BuildRequires:  libdrm-devel
BuildRequires:  libglvnd-devel
BuildRequires:  libzstd-devel
BuildRequires:  mesa-libgbm-devel
BuildRequires:  pam-devel
BuildRequires:  polkit-devel
BuildRequires:  pkgconfig(libpipewire-0.3)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtbase-private-devel
BuildRequires:  qt6-qtdeclarative-devel
BuildRequires:  qt6-qtshadertools-devel
BuildRequires:  qt6-qtsvg-devel
BuildRequires:  qt6-qtwayland-devel
BuildRequires:  spirv-tools
BuildRequires:  vulkan-headers
BuildRequires:  wayland-protocols-devel

%description
Quickshell: status bars, widgets, lockscreens, and other desktop
components in QML, for Wayland compositors (here: Mango). No default
shell config is shipped — the user owns ~/.config/quickshell.

%prep
%autosetup -n quickshell-%{version} -p1

%build
%cmake -GNinja -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_bindir}/qs
%{_libdir}/qt6/qml/Quickshell/

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.3.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe, full feature set)
