%global xdg_desktop_portal_version 1.19.1

Name:           xdg-desktop-portal-gtk
Version:        1.15.3
Release:        %autorelease
Summary:        Backend implementation for xdg-desktop-portal using GTK+

License:        LGPL-2.0-or-later
URL:            https://github.com/flatpak/%{name}
Source0:        https://github.com/flatpak/%{name}/releases/download/%{version}/%{name}-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  meson
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(gsettings-desktop-schemas)
BuildRequires:  pkgconfig(gtk+-unix-print-3.0)
BuildRequires:  pkgconfig(xdg-desktop-portal) >= %{xdg_desktop_portal_version}
BuildRequires:  systemd-rpm-macros
Requires:       dbus
Requires:       gsettings-desktop-schemas
Requires:       xdg-desktop-portal >= %{xdg_desktop_portal_version}

# https://github.com/containers/composefs/pull/229#issuecomment-1838735764
%if 0%{?rhel} >= 10
ExcludeArch:    %{ix86}
%endif

# This portal is recommended if you have installed any app that uses GTK. (It's
# also recommended if you have any such app installed via flatpak or snap, but
# that is impossible to detect here.)
Supplements:    gtk3
Supplements:    gtk4

%description
A backend implementation for xdg-desktop-portal that is using GTK+.


%prep
%autosetup -p1


%build
# All backends that are disabled are instead provided by
# xdg-desktop-portal-gnome, to keep this package free of GNOME dependencies.
# The appchooser and settings backends are enabled for non-GNOME GTK
# applications.
%meson \
    -Dappchooser=enabled \
    -Dsettings=enabled \
    -Dlockdown=disabled \
    -Dwallpaper=disabled \
    %{nil}
%meson_build


%install
%meson_install
%find_lang %{name}


%post
%systemd_user_post %{name}.service

%preun
%systemd_user_preun %{name}.service


%files -f %{name}.lang
%license COPYING
%doc NEWS README.md
%{_libexecdir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.gtk.service
%{_datadir}/xdg-desktop-portal/portals/gtk.portal
%{_userunitdir}/%{name}.service



%changelog
%autochangelog
