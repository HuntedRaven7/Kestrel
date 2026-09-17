# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/mangowm/mango (tag 0.17.2).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build). Requires wlroots-0.20 + scenefx-0.5.

Name:           mango
Version:        0.17.2
Release:        1.hum1.pigeon
Summary:        Fast, feature-rich Wayland compositor (Mango)
License:        GPL-3.0-only
URL:            https://github.com/mangowm/mango
Source0:        https://github.com/mangowm/mango/archive/refs/tags/%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libinput) >= 1.27.1
BuildRequires:  pkgconfig(libpcre2-8)
BuildRequires:  pkgconfig(libcjson)
BuildRequires:  pkgconfig(pangocairo)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(scenefx-0.5) >= 0.5.0
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-server) >= 1.23.1
BuildRequires:  pkgconfig(wlroots-0.20) >= 0.20.0
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(xcb-icccm)
BuildRequires:  pkgconfig(xcb-randr)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  wayland-devel
BuildRequires:  wayland-protocols-devel

%description
Mango Wayland compositor: dwl-based, tags-not-workspaces, animations,
window effects via scenefx, IPC via mmsg. Ships its GDM session file,
default config, and systemd session target.

%prep
%autosetup -n mango-%{version} -p1

%build
%meson
%meson_build

%install
%meson_install

%files
%license LICENSE
%{_bindir}/mango
%{_bindir}/mmsg
%{_datadir}/wayland-sessions/mango.desktop
%{_datadir}/xdg-desktop-portal/mango-portals.conf
%{_userunitdir}/mango-session.target
%{_mandir}/man1/mmsg.1*
%config(noreplace) %{_sysconfdir}/mango/config.conf

%changelog
* Wed Sep 17 2026 Kestrel <kestrel@localhost> - 0.17.2-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
