# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/flatpak/flatpak-xdg-utils (tag 1.0.6).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:     flatpak-xdg-utils
Summary:  Command-line tools for use inside Flatpak sandboxes
Version:  1.0.6
Release:  1.hum1.pigeon
License:  LGPL-2.0-or-later AND LGPL-2.1-or-later
URL:      https://github.com/flatpak/flatpak-xdg-utils
Source:   https://github.com/flatpak/flatpak-xdg-utils/releases/download/1.0.6/flatpak-xdg-utils-1.0.6.tar.xz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  pkgconfig(glib-2.0)

Requires: flatpak-spawn%{?_isa} = %{version}-%{release}

%description
This package contains a number of command-line utilities for use inside
Flatpak sandboxes. They work by talking to portals.

%package -n     flatpak-spawn
Summary:        Command-line frontend for the org.freedesktop.Flatpak service
License:        LGPL-2.1-or-later

%description -n flatpak-spawn
This package contains the flatpak-spawn command-line utility. It can be
used to talk to the org.freedesktop.Flatpak service to spawn new sandboxes,
run commands on the host, or use one of the session or system helpers.

%package tests
Summary:   Tests for %{name}
License:   LGPL-2.1-or-later AND MIT
Requires:  %{name}%{?_isa} = %{version}-%{release}
Requires:  flatpak-spawn%{?_isa} = %{version}-%{release}

%description tests
This package contains installed tests for %{name}.

%prep
%autosetup -n flatpak-xdg-utils-1.0.6

%build
%meson -Dinstalled_tests=true
%meson_build

%install
%meson_install

mv %{buildroot}%{_bindir}/xdg-email %{buildroot}%{_bindir}/flatpak-xdg-email
mv %{buildroot}%{_bindir}/xdg-open %{buildroot}%{_bindir}/flatpak-xdg-open

%files
%license COPYING
%{_bindir}/flatpak-xdg-email
%{_bindir}/flatpak-xdg-open
%{_bindir}/flatpak-xdg-list

%files -n flatpak-spawn
%license COPYING
%{_bindir}/flatpak-spawn

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 1.0.6-1.hum1.pigeon
- Initial Kestrel package (independent recipe)