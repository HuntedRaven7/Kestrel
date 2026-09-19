# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/ximion/appstream (tag 1.1.3).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%bcond blake3 0
%bcond stemming 0

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
%if %{with blake3}
BuildRequires: pkgconfig(libblake3)
%endif
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

%package compose
Summary: Library for generating AppStream data
Requires: %{name}%{?_isa} = %{version}-%{release}
%description compose
%{summary}.

%prep
%autosetup -n AppStream-1.1.3

%build
%meson \
  -Dblake3=%{with blake3} \
  -Dstemming=%{with stemming} \
  -Ddocs=true \
  -Dman=true
%meson_build

%install
%meson_install

%files
%license COPYING
%{_bindir}/*
%{_libdir}/libappstream*.so.*
%{_libdir}/girepository-1.0/
%{_datadir}/gir-1.0/
%{_datadir}/appstream/
%{_datadir}/bash-completion/completions/

%files devel
%license COPYING
%{_libdir}/libappstream*.so
%{_libdir}/pkgconfig/appstream*.pc
%{_includedir}/appstream*

%files compose
%license COPYING
%{_libdir}/libappstream-compose*.so.*
%{_libdir}/pkgconfig/appstream-compose.pc
%{_includedir}/appstream-compose*

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.1.3-1.hum1.pigeon
- Initial Kestrel package (independent recipe)