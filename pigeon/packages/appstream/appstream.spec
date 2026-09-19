# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/ximion/appstream (tag 1.1.3).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%bcond stemming 0
%bcond qt 1
%bcond blake3 0

Summary: Utilities to generate, maintain and access the AppStream database
Name:    appstream
Version: 1.1.3
Release: 1.hum1.pigeon

License: GPL-2.0-or-later AND LGPL-2.1-or-later
URL:     https://github.com/ximion/appstream
Source0: https://github.com/ximion/appstream/archive/refs/tags/v%{version}.tar.gz

BuildRequires: cmake
BuildRequires: docbook5-style-xsl
BuildRequires: meson >= 0.62
BuildRequires: gettext
BuildRequires: git-core
BuildRequires: gperf
BuildRequires: gtk-doc
BuildRequires: intltool
BuildRequires: itstool
%if %{with stemming}
BuildRequires: libstemmer-devel
%endif
BuildRequires: pkgconfig(bash-completion)
BuildRequires: pkgconfig(cairo)
BuildRequires: pkgconfig(freetype2)
BuildRequires: pkgconfig(fontconfig)
BuildRequires: pkgconfig(gdk-pixbuf-2.0)
BuildRequires: pkgconfig(gi-docgen) >= 2021.1
BuildRequires: pkgconfig(gio-2.0)
BuildRequires: pkgconfig(gobject-introspection-1.0)
BuildRequires: pkgconfig(libcurl)
BuildRequires: pkgconfig(libfyaml)
BuildRequires: pkgconfig(librsvg-2.0)
BuildRequires: pkgconfig(libsystemd)
BuildRequires: pkgconfig(libxml-2.0)
BuildRequires: pkgconfig(libzstd)
BuildRequires: pkgconfig(pango)
BuildRequires: pkgconfig(Qt6Core) >= 6.2.4
BuildRequires: pkgconfig(xmlb) >= 0.3.14
BuildRequires: pkgconfig(yaml-0.1)
BuildRequires: qt6-linguist
BuildRequires: sed
BuildRequires: vala
BuildRequires: xmlto

Requires: (appstream-data if (PackageKit or libdnf5-plugin-appstream))

%description
AppStream makes it easy to access application information from the
AppStream database over a nice GObject-based interface.

%package devel
Summary:  Development files for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}
Obsoletes: appstream-vala < 0.12.4-3
Provides: appstream-vala = %{version}-%{release}
%description devel
%{summary}.

%package qt
Summary: Qt6 bindings for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}

%description qt
%{summary}.

%package qt-devel
Summary: Development files for %{name}-qt bindings
Requires: %{name}-qt%{?_isa} = %{version}-%{release}
Requires: pkgconfig(Qt6Core) >= 6.2.4

%description qt-devel
%{summary}.

%prep
%autosetup -n appstream-%{version}

%build
%meson \
  -Dcompose=true \
  -Dqt=%{?with_qt:true}%{!?with_qt:false} \
  -Dblake3-support=%{?with_blake3:true}%{!?with_blake3:false} \
  -Dstemming=%{?with_stemming:true}%{!?with_stemming:false} \
  -Dvapi=true \
  -Ddocs=false \
  -Dman=true
%meson_build

%install
%meson_install

%find_lang appstream

mkdir -p %{buildroot}/var/cache/swcatalog/{icons,gv,xml}
touch %{buildroot}/var/cache/swcatalog/cache.watch

%files -f appstream.lang
%license COPYING
%{_bindir}/appstreamcli
%{_mandir}/man1/appstreamcli.1*
%{_datadir}/bash-completion/completions/appstreamcli
%{_datadir}/appstream/
%dir %{_libdir}/girepository-1.0/
%{_libdir}/girepository-1.0/AppStream-1.0.typelib
%{_libdir}/libappstream.so.5
%{_libdir}/libappstream.so.%{version}
%{_metainfodir}/org.freedesktop.appstream.cli.*.xml
# put in -devel? -- rex
%{_datadir}/gettext/its/metainfo.*
%ghost /var/cache/swcatalog/cache.watch
%dir /var/cache/swcatalog/
%dir /var/cache/swcatalog/icons/
%dir /var/cache/swcatalog/gv/
%dir /var/cache/swcatalog/xml/

%files devel
%license COPYING
%{_includedir}/appstream/
%{_libdir}/libappstream.so
%{_libdir}/pkgconfig/appstream.pc
%dir %{_datadir}/gir-1.0/
%{_datadir}/gir-1.0/AppStream-1.0.gir
%dir %{_datadir}/vala
%dir %{_datadir}/vala/vapi
%{_datadir}/vala/vapi/appstream.deps
%{_datadir}/vala/vapi/appstream.vapi
%{_docdir}/appstream/html/

%files compose
%license COPYING
%{_libexecdir}/appstreamcli-compose
%{_mandir}/man1/appstreamcli-compose.1*
%{_libdir}/libappstream-compose.so.0
%{_libdir}/libappstream-compose.so.%{version}
%{_libdir}/girepository-1.0/AppStreamCompose-1.0.typelib
%{_metainfodir}/org.freedesktop.appstream.compose.metainfo.xml

%files compose-devel
%{_includedir}/appstream-compose/
%{_libdir}/libappstream-compose.so
%{_libdir}/pkgconfig/appstream-compose.pc
%{_datadir}/gir-1.0/AppStreamCompose-1.0.gir
%dir %{_datadir}/gtk-doc/
%dir %{_datadir}/gtk-doc/html/
%{_datadir}/gtk-doc/html/appstream-compose

%files qt
%{_libdir}/libAppStreamQt.so.3
%{_libdir}/libAppStreamQt.so.%{version}

%files qt-devel
%{_includedir}/AppStreamQt/
%{_libdir}/cmake/AppStreamQt/
%{_libdir}/libAppStreamQt.so

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.1.3-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
- Enable compose and qt libraries, add compose-devel/qt/qt-devel subpackages
- Add %find_lang for translations