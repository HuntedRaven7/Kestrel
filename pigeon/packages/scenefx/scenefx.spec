# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/wlrfx/scenefx (tag 0.5).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build). Built against our wlroots0.20.

Name:           scenefx
Version:        0.5
Release:        1.hum1.pigeon
Summary:        Scene graph and effects library for wlroots compositors
License:        MIT
URL:            https://github.com/wlrfx/scenefx
Source0:        https://github.com/wlrfx/scenefx/archive/refs/tags/%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  meson >= 1.3
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(wlroots-0.20)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  wayland-protocols-devel

%description
scenefx 0.5.x: blur, shadows, corner radius, and animations for
wlroots-based compositors (here: Mango).

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkgconfig file, and the unversioned .so link for scenefx 0.5.

%prep
%autosetup -n scenefx-%{version} -p1

%build
%meson -Dexamples=false
%meson_build

%install
%meson_install

%ldconfig_scriptlets

%files
%license LICENSE
%{_libdir}/libscenefx-0.5.so.*

%files devel
%{_includedir}/scenefx-0.5/
%{_libdir}/libscenefx-0.5.so
%{_libdir}/pkgconfig/scenefx-0.5.pc

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.5-1.hum1.pigeon
- Initial Kestrel package (independent recipe, wlroots-0.20 backend)
