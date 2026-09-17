%bcond check 1

%global glib2_version %(pkg-config --modversion glib-2.0 2>/dev/null || echo bad)
%global qmi_version %(pkg-config --modversion qmi-glib 2>/dev/null || echo bad)
%global mbim_version %(pkg-config --modversion mbim-glib 2>/dev/null || echo bad)
%global qrtr_version %(pkg-config --modversion qrtr-glib 2>/dev/null || echo bad)

%global forgeurl https://gitlab.freedesktop.org/mobile-broadband/ModemManager

Name: ModemManager
Version: 1.24.2
Release: %autorelease
Summary: Mobile broadband modem management service
License: GPL-2.0-or-later
URL: %{forgeurl}
Source: %{forgeurl}/-/archive/%{version}/%{name}-%{version}.tar.bz2

# For mbim-proxy and qmi-proxy
Requires: libmbim-utils
Requires: libqmi-utils
Requires: %{name}-glib%{?_isa} = %{version}-%{release}

# Don't allow older versions of these than what we built against,
# because they add new API w/o versioning it or bumping the SONAME
Conflicts: glib2%{?_isa} < %{glib2_version}
Conflicts: libqmi%{?_isa} < %{qmi_version}
Conflicts: libmbim%{?_isa} < %{mbim_version}
Conflicts: libqrtr-glib%{?_isa} < %{qrtr_version}

Requires(post): systemd
Requires(postun): systemd
Requires(preun): systemd

Requires: polkit
# xxd is needed by the FCC unlock script for 14c3 (#2440074)
Recommends: xxd

BuildRequires: meson >= 0.53
BuildRequires: dbus-devel
BuildRequires: dbus-daemon
BuildRequires: gettext-devel >= 0.19.8
BuildRequires: glib2-devel >= 2.56
BuildRequires: gobject-introspection-devel >= 1.38
BuildRequires: gtk-doc
BuildRequires: libgudev1-devel >= 232
BuildRequires: libmbim-devel >= 1.32.0
BuildRequires: libqmi-devel >= 1.36.0
BuildRequires: libqrtr-glib-devel >= 1.0.0
BuildRequires: systemd
BuildRequires: systemd-devel >= 209
BuildRequires: vala
BuildRequires: polkit-devel
%if %{with check}
BuildRequires: python3-gobject
BuildRequires: python3-dbus
%endif

%global __provides_exclude ^libmm-plugin-

%description
The ModemManager service manages WWAN modems and provides a consistent API for
interacting with these devices to client applications.


%package devel
Summary: Libraries and headers for adding ModemManager support to applications
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: pkgconfig

%description devel
This package contains various headers for accessing some ModemManager functionality
from applications.


%package glib
Summary: Libraries for adding ModemManager support to applications that use glib.
License: LGPL-2.1-or-later
Requires: glib2 >= %{glib2_version}

%description glib
This package contains the libraries that make it easier to use some ModemManager
functionality from applications that use glib.


%package glib-devel
Summary: Libraries and headers for adding ModemManager support to applications that use glib.
License: LGPL-2.1-or-later
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
Requires: %{name}-glib%{?_isa} = %{version}-%{release}
Requires: glib2-devel >= %{glib2_version}
Requires: pkgconfig

%description glib-devel
This package contains various headers for accessing some ModemManager functionality
from glib applications.


%package vala
Summary: Vala bindings for ModemManager
License: LGPL-2.1-or-later
Requires: vala
Requires: %{name}-glib%{?_isa} = %{version}-%{release}

%description vala
Vala bindings for ModemManager


%prep
%autosetup -p1


%build
# Let's avoid BuildRequiring bash-completion because it changes behavior
# of shell, at least until the .pc file gets into the -devel subpackage.
# We'll just install the bash-completion file ourselves.
%meson \
	-Ddist_version='"%{version}-%{release}"' \
	-Dudevdir=/usr/lib/udev \
	-Dsystemdsystemunitdir=%{_unitdir} \
	-Ddbus_policy_dir=%{_datadir}/dbus-1/system.d \
	-Dvapi=true \
	-Dgtk_doc=true \
	-Dpolkit=permissive \
	-Dbash_completion=false
%meson_build


%install
%meson_install
find %{buildroot}%{_datadir}/gtk-doc |xargs touch --reference meson.build
%find_lang %{name}
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions/
cp -a cli/mmcli-completion %{buildroot}%{_datadir}/bash-completion/completions/mmcli

%if %{with check}
%check
%meson_test
%endif


%post
%systemd_post ModemManager.service


%preun
%systemd_preun ModemManager.service


%postun
%systemd_postun ModemManager.service


%files -f %{name}.lang
%license COPYING
%doc README.md
%{_datadir}/dbus-1/system.d/org.freedesktop.ModemManager1.conf
%{_datadir}/dbus-1/system-services/org.freedesktop.ModemManager1.service
%attr(0755,root,root) %{_sbindir}/ModemManager
%attr(0755,root,root) %{_bindir}/mmcli
%dir %{_libdir}/%{name}
%attr(0755,root,root) %{_libdir}/%{name}/*.so*
%{_udevrulesdir}/*
%{_datadir}/polkit-1/actions/*.policy
%{_unitdir}/ModemManager.service
%{_datadir}/icons/hicolor/22x22/apps/*.png
%{_datadir}/bash-completion
%{_datadir}/ModemManager
%{_mandir}/man1/*
%{_mandir}/man8/*


%files devel
%{_includedir}/ModemManager/
%dir %{_datadir}/gtk-doc/html/%{name}
%{_datadir}/gtk-doc/html/%{name}/*
%{_libdir}/pkgconfig/%{name}.pc
%{_datadir}/dbus-1/interfaces/*.xml


%files glib
%license COPYING
%{_libdir}/libmm-glib.so.*
%{_libdir}/girepository-1.0/*.typelib


%files glib-devel
%{_libdir}/libmm-glib.so
%dir %{_includedir}/libmm-glib
%{_includedir}/libmm-glib/*.h
%{_libdir}/pkgconfig/mm-glib.pc
%dir %{_datadir}/gtk-doc/html/libmm-glib
%{_datadir}/gtk-doc/html/libmm-glib/*
%{_datadir}/gir-1.0/*.gir


%files vala
%{_datadir}/vala/vapi/libmm-glib.*


%changelog
%autochangelog
