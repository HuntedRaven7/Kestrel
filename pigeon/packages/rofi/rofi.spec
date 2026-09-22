# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/davatorium/rofi (tag 1.7.9.1).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build). Stock rofi = X11, runs under
# Mango via XWayland.

Name:           rofi
Version:        2.0.0
Release:        1.hum1.pigeon
Summary:        Window switcher, run dialog, and dmenu replacement
License:        MIT
URL:            https://github.com/davatorium/rofi
Source0:        https://github.com/davatorium/rofi/archive/refs/tags/%{version}.tar.gz
# Submodules (git archives don't include submodule contents)
Source1:        libgwater-master.tar.gz
Source2:        libnkutils-master.tar.gz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  pandoc
BuildRequires:  flex
BuildRequires:  bison
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(cairo-xcb)
BuildRequires:  pkgconfig(gdk-pixbuf-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gmodule-2.0)
BuildRequires:  pkgconfig(libstartup-notification-1.0)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(pangocairo)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(xcb-aux)
BuildRequires:  pkgconfig(xcb-cursor)
BuildRequires:  pkgconfig(xcb-ewmh)
BuildRequires:  pkgconfig(xcb-icccm)
BuildRequires:  pkgconfig(xcb-keysyms)
BuildRequires:  pkgconfig(xcb-randr)
BuildRequires:  pkgconfig(xcb-xinerama)
BuildRequires:  pkgconfig(xcb-xkb)
BuildRequires:  pkgconfig(xcb-imdkit)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(xkbcommon-x11)

%description
Rofi launcher for the Warbler desktop (drun + window modes).

%prep
%autosetup -n rofi-%{version} -p1
# Populate submodule subprojects. Source1/Source2 are declared as
# extra_sources in upstream-sources.json and staged by source_pipeline.py
# fetch (hash-verified, commit-pinned) — no network access here.
tar -xzf %{SOURCE1} -C subprojects/libgwater --strip-components=1
tar -xzf %{SOURCE2} -C subprojects/libnkutils --strip-components=1

%build
%meson -Dcheck=disabled
%meson_build

%install
%meson_install

%files
%license COPYING
%{_bindir}/rofi*
%{_includedir}/rofi/
%{_libdir}/pkgconfig/rofi.pc
%{_datadir}/rofi/
%{_datadir}/applications/rofi*.desktop
%{_datadir}/icons/hicolor/scalable/apps/rofi.svg
%{_mandir}/man1/rofi*
%{_mandir}/man5/rofi*

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 1.7.9.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
