# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream mirror: https://github.com/quickshell-mirror/quickshell (tag v0.3.1,
# GPG-signed 1a4716c). Canonical upstream: https://git.outfoxxed.me/quickshell/quickshell
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
# CAUTION: Quickshell uses private Qt APIs — rebuild on EVERY Qt update
# (Renovate group qt-quickshell couples them).

Name:           quickshell
Version:        0.3.1
Release:        1.hum1.rpmfactory
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
# INSTALL_QMLDIR: without it upstream skips QML module install entirely
# (and %files expects them under %%{_libdir}/qt6/qml).
# Fedora's cpptrace-devel is built without the optional libunwind backend;
# Quickshell's upstream check rejects that configuration.  Keep the build
# hermetic (the vendor fallback would fetch cpptrace during rpmbuild) and use
# the system library's supported non-signal-safe unwind path.
%cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DINSTALL_QMLDIR=%{_libdir}/qt6/qml -DDO_NOT_CHECK_CPPTRACE_USABILITY=ON
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_bindir}/quickshell
%{_bindir}/qs
%{_libdir}/qt6/qml/Quickshell/
%{_datadir}/applications/org.quickshell.desktop
%{_datadir}/icons/hicolor/scalable/apps/org.quickshell.svg

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.3.1-1.hum1.rpmfactory
- Initial Kestrel package (independent recipe, full feature set)
