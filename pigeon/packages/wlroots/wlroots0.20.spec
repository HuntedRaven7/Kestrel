# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://gitlab.freedesktop.org/wlroots/wlroots (tag 0.20.2).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build). Mango 0.17.2 requires wlroots-0.20;
# the versioned name/SONAME keeps this parallel-installable alongside any
# other wlroots generation the base OS ships.

Name:           wlroots0.20
Version:        0.20.2
Release:        1.hum1.pigeon
Summary:        Modular Wayland compositor library (0.20.x for Mango)
License:        MIT
URL:            https://gitlab.freedesktop.org/wlroots/wlroots
Source0:        https://gitlab.freedesktop.org/wlroots/wlroots/-/archive/%{version}/wlroots-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  meson >= 1.3
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(gbm) >= 17.1.0
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(lcms2)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libdisplay-info)
BuildRequires:  pkgconfig(libinput)
BuildRequires:  pkgconfig(libliftoff)
BuildRequires:  pkgconfig(libseat)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(vulkan)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-egl)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(xwayland)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(xcb-composite)
BuildRequires:  pkgconfig(xcb-dri3)
BuildRequires:  pkgconfig(xcb-errors)
BuildRequires:  pkgconfig(xcb-ewmh)
BuildRequires:  pkgconfig(xcb-icccm)
BuildRequires:  pkgconfig(xcb-present)
BuildRequires:  pkgconfig(xcb-render)
BuildRequires:  pkgconfig(xcb-renderutil)
BuildRequires:  pkgconfig(xcb-res)
BuildRequires:  pkgconfig(xcb-shm)
BuildRequires:  pkgconfig(xcb-xfixes)
BuildRequires:  pkgconfig(xcb-xinput)
BuildRequires:  wayland-protocols-devel
BuildRequires:  hwdata

%description
wlroots 0.20.x, packaged versioned so Mango (which pins wlroots-0.20)
builds regardless of the wlroots generation the base OS carries.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       pkgconfig(wayland-server)

%description devel
Headers, pkgconfig file, and the unversioned .so link for wlroots 0.20.

%prep
%autosetup -n wlroots-%{version} -p1

%build
%meson -Dexamples=false
%meson_build

%install
%meson_install

%ldconfig_scriptlets

%files
%license LICENSE
%{_libdir}/libwlroots-0.20.so.*

%files devel
%{_includedir}/wlroots-0.20/
%{_libdir}/libwlroots-0.20.so
%{_libdir}/pkgconfig/wlroots-0.20.pc

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 0.20.2-1.hum1.pigeon
- Initial Kestrel package (independent recipe for Mango 0.17.2)
