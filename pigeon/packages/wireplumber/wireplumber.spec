# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/pipewire/wireplumber (tag 0.5.8).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           wireplumber
Version:        0.5.8
Release:        1.hum1.pigeon
Summary:        Session / policy manager implementation for PipeWire
License:        MIT
URL:            https://github.com/pipewire/wireplumber
Source0:        https://github.com/pipewire/wireplumber/archive/refs/tags/0.5.8/wireplumber-0.5.8.tar.gz

BuildRequires:  meson >= 0.55.0
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(gobject-2.0)
BuildRequires:  pkgconfig(glib-2.0) >= 2.70.0
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(libpipewire-0.3)
BuildRequires:  pkgconfig(lua) >= 5.1
BuildRequires:  lua-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  gobject-introspection-devel
BuildRequires:  lua-devel

Requires:       pipewire >= 1.0.0
Requires:       systemd

%description
WirePlumber is a session / policy manager implementation for PipeWire.
It manages the graph of PipeWire nodes and links, and provides
a Lua scripting API for policy configuration.

%prep
%autosetup -n wireplumber-0.5.8 -p1

%build
%meson \
  -Dsystemd=true \
  -Dsystemd_system_unit_dir=%{_unitdir} \
  -Dsystemd_user_unit_dir=%{_userunitdir} \
  -Ddoc=enabled \
  -Dinstalled_tests=true \
  -Dlua-interpreter=lua \
  -Dsystem-lua=true
%meson_build

%install
%meson_install

%post
%systemd_post wireplumber.service
%systemd_user_post wireplumber.service

%preun
%systemd_preun wireplumber.service
%systemd_user_preun wireplumber.service

%postun
%systemd_postun wireplumber.service
%systemd_user_postun wireplumber.service

%files
%license COPYING
%{_bindir}/wireplumber
%{_bindir}/wplua
%{_libdir}/wireplumber/
%{_libdir}/libwireplumber-*.so.*
%{_libdir}/girepository-1.0/WirePlumber-*.typelib
%{_datadir}/wireplumber/
%{_datadir}/gir-1.0/WirePlumber-*.typelib
%{_datadir}/dbus-1/services/org.freedesktop.WirePlumber.service
%{_userunitdir}/wireplumber.service
%{_datadir}/gir-1.0/WirePlumber-*.typelib
%{_mandir}/man1/wireplumber.1*
%{_mandir}/man1/wplua.1*

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 0.5.8-1.hum1.pigeon
- Initial Kestrel package (independent recipe)