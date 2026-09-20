# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/flatpak/flatpak (tag 1.19.0).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%global appstream_version 1.0.0~
%global bubblewrap_version 0.10.0
%global glib_version 2.46.0
%global gpgme_version 1.8.0
%global libcurl_version 7.29.0
%global ostree_version 2020.8
%global wayland_protocols_version 1.32
%global wayland_scanner_version 1.15
%global xdg_portal_version 1.7.0

Name:           flatpak
Version:        1.19.0
Release:        1.hum1.pigeon
Summary:        Application deployment framework for desktop apps

License:        LGPL-2.1-or-later
URL:            https://flatpak.org/
Source0:        https://github.com/flatpak/flatpak/releases/download/%{version}/%{name}-%{version}.tar.xz

%if 0%{?fedora}
Source1:        flatpak-add-fedora-repos.service
%endif

BuildRequires:  pkgconfig(appstream) >= 1.0.0~
BuildRequires:  pkgconfig(dconf)
BuildRequires:  pkgconfig(fuse3)
BuildRequires:  pkgconfig(gdk-pixbuf-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0) >= 2.46.0
BuildRequires:  pkgconfig(gobject-introspection-1.0) >= 1.40.0
BuildRequires:  pkgconfig(gpgme) >= 1.8.0
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(libarchive) >= 2.8.0
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(libcurl) >= 7.29.0
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(libxml-2.0) >= 2.4
BuildRequires:  pkgconfig(libzstd) >= 0.8.1
BuildRequires:  pkgconfig(ostree-1) >= 2020.8
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.32
BuildRequires:  pkgconfig(wayland-scanner) >= 1.15
BuildRequires:  pkgconfig(xau)
BuildRequires:  pkgconfig(malcontent-0)
BuildRequires:  bison
BuildRequires:  bubblewrap >= 0.10.0
BuildRequires:  docbook-dtds
BuildRequires:  docbook-style-xsl
BuildRequires:  gettext-devel
BuildRequires:  gtk-doc
BuildRequires:  libcap-devel
BuildRequires:  meson
BuildRequires:  python3-pyparsing
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
BuildRequires:  /usr/bin/fusermount3
BuildRequires:  /usr/bin/pkcheck
BuildRequires:  /usr/bin/socat
BuildRequires:  /usr/bin/xdg-dbus-proxy
BuildRequires:  /usr/bin/xmlto
BuildRequires:  /usr/bin/xsltproc
BuildRequires:  selinux-policy-devel

Requires:       appstream%{?_isa} >= 1.0.0~
Requires:       bubblewrap >= 0.10.0
Requires:       glib2%{?_isa} >= 2.46.0
Requires:       libcurl%{?_isa} >= 7.29.0
Requires:       librsvg2%{?_isa}
Requires:       ostree-libs%{?_isa} >= 2020.8
Requires:       /usr/bin/fusermount3
Requires:       /usr/bin/xdg-dbus-proxy
Requires:       (flatpak-selinux = %{?epoch:%{epoch}:}%{version}-%{release} if selinux-policy-targeted)
Requires:       %{name}-session-helper%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Recommends:     p11-kit-server
Recommends:     xdg-desktop-portal >= 1.7.0

%description
flatpak is a system for building, distributing and running sandboxed desktop
applications on Linux.

%package devel
Summary:        Development files for %{name}
%description devel
%{summary}.

%package session-helper
Summary:        Session helper for flatpak
Requires:       flatpak = %{version}-%{release}

%description session-helper
%{summary}.

%prep
%autosetup -n flatpak-1.19.0 -p1

%build
%meson \
  -Dsystemd=enabled \
  -Dsystemduserunitdir=/usr/lib/systemd/user \
  -Dsystemdsystemunitdir=%{_unitdir} \
  -Dselinux_module=disabled \
  -Dsystem_bubblewrap=/usr/bin/bwrap \
  -Dsystem_dbus_proxy=/usr/bin/xdg-dbus-proxy \
  -Dinstalled_tests=false \
  -Dtmpfilesdir=%{_tmpfilesdir} \
  -Dwayland_security_context=enabled
%meson_build

%install
%meson_install
%find_lang flatpak

# Directories the build system does not create but %files expects
install -d %{buildroot}%{_datadir}/%{name}/preinstall.d
install -d %{buildroot}%{_datadir}/%{name}/remotes.d
install -d %{buildroot}%{_localstatedir}/lib/flatpak
install -d %{buildroot}%{_sysconfdir}/%{name}/installations.d
install -d %{buildroot}%{_sysconfdir}/%{name}/preinstall.d
install -d %{buildroot}%{_sysconfdir}/flatpak/remotes.d

%if 0%{?fedora}
install -D -p -m 0644 -t %{buildroot}%{_unitdir} %{SOURCE1}
%endif

%post
systemctl --user daemon-reload >/dev/null 2>&1 || :
systemctl daemon-reload >/dev/null 2>&1 || :

%postun
systemctl --user daemon-reload >/dev/null 2>&1 || :
systemctl daemon-reload >/dev/null 2>&1 || :

%post session-helper
systemctl --user daemon-reload >/dev/null 2>&1 || :

%postun session-helper
systemctl --user daemon-reload >/dev/null 2>&1 || :

%files -f flatpak.lang
%license COPYING
%doc NEWS README.md
%{_bindir}/flatpak
%{_bindir}/flatpak-bisect
%{_bindir}/flatpak-coredumpctl
%{_libdir}/libflatpak*.so.*
%{_libdir}/girepository-1.0/Flatpak-1.0.typelib
%{_libexecdir}/flatpak-oci-authenticator
%{_libexecdir}/flatpak-portal
%{_libexecdir}/flatpak-system-helper
%{_libexecdir}/flatpak-validate-icon
%{_libexecdir}/revokefs-fuse
%{_datadir}/bash-completion
%{_datadir}/dbus-1/interfaces/org.freedesktop.portal.Flatpak.xml
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.Authenticator.xml
%{_datadir}/dbus-1/services/org.flatpak.Authenticator.Oci.service
%{_datadir}/dbus-1/services/org.freedesktop.portal.Flatpak.service
%{_datadir}/dbus-1/system.d/org.freedesktop.Flatpak.SystemHelper.conf
%{_datadir}/dbus-1/system-services/org.freedesktop.Flatpak.SystemHelper.service
%{_datadir}/polkit-1/actions/org.freedesktop.Flatpak.policy
%{_datadir}/polkit-1/rules.d/org.freedesktop.Flatpak.rules
%{_datadir}/flatpak/
%{_datadir}/fish/
%{_datadir}/zsh/site-functions
%dir %{_localstatedir}/lib/flatpak
%dir %{_sysconfdir}/flatpak
%{_sysconfdir}/flatpak/installations.d
%{_sysconfdir}/flatpak/preinstall.d
%{_sysconfdir}/flatpak/remotes.d
%{_sysconfdir}/profile.d/flatpak.csh
%{_sysconfdir}/profile.d/flatpak.sh
%{_mandir}/man1/flatpak*.1*
%{_mandir}/man5/flatpak*.5*
%{_sysusersdir}/flatpak.conf
%{_tmpfilesdir}/flatpak.conf
%{_unitdir}/flatpak-system-helper.service
%{_userunitdir}/flatpak-oci-authenticator.service
%{_userunitdir}/flatpak-portal.service
%{_systemd_system_env_generator_dir}/60-flatpak-system-only
%{_systemd_user_env_generator_dir}/60-flatpak

%if 0%{?fedora}
%{_unitdir}/flatpak-add-fedora-repos.service
%endif

%files session-helper
%license COPYING
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.xml
%{_datadir}/dbus-1/services/org.freedesktop.Flatpak.service
%{_libexecdir}/flatpak-session-helper
%{_userunitdir}/flatpak-session-helper.service

%files devel
%{_datadir}/gir-1.0/Flatpak-1.0.gir
%{_datadir}/gtk-doc/
%{_docdir}/flatpak/
%{_libdir}/pkgconfig/flatpak.pc
%{_libdir}/libflatpak.so
%{_includedir}/flatpak/

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.19.0-1.hum1.pigeon
- Initial Kestrel package (independent recipe)