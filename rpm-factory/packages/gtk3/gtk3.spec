%if 0%{?fedora}
%global with_broadway 1
%global with_cloudproviders 1
%endif

%global glib2_version 2.57.2
%global pango_version 1.41.0
%global atk_version 2.35.1
%global cairo_version 1.14.0
%global gdk_pixbuf_version 2.30.0
%global xrandr_version 1.5.0
%global wayland_protocols_version 1.17
%global wayland_version 1.14.91
%global epoxy_version 1.4

%global bin_version 3.0.0

# Filter provides for private modules
%global __provides_exclude_from ^%{_libdir}/gtk-3.0

Name:    gtk3
Version: 3.24.52
Release: %autorelease
Summary: GTK+ graphical user interface library

License: LGPL-2.0-or-later
URL:     https://gtk.org
Source0: https://download.gnome.org/sources/gtk/%{gnome_major_minor_version}/gtk-%{version}.tar.xz
Patch0:  9852_export_xdg_toplevel.patch
Patch1:  9956_pointer_focus.patch

BuildRequires: pkgconfig(atk) >= %{atk_version}
BuildRequires: pkgconfig(atk-bridge-2.0)
BuildRequires: pkgconfig(avahi-gobject)
BuildRequires: pkgconfig(cairo) >= %{cairo_version}
BuildRequires: pkgconfig(cairo-gobject) >= %{cairo_version}
%if 0%{?with_cloudproviders}
BuildRequires: pkgconfig(cloudproviders)
%endif
BuildRequires: pkgconfig(colord)
BuildRequires: pkgconfig(egl)
BuildRequires: pkgconfig(epoxy)
BuildRequires: pkgconfig(gdk-pixbuf-2.0) >= %{gdk_pixbuf_version}
BuildRequires: pkgconfig(glib-2.0) >= %{glib2_version}
BuildRequires: pkgconfig(gobject-introspection-1.0)
BuildRequires: pkgconfig(pango) >= %{pango_version}
BuildRequires: pkgconfig(sysprof-capture-4)
BuildRequires: pkgconfig(tracker-sparql-3.0)
BuildRequires: pkgconfig(wayland-client) >= %{wayland_version}
BuildRequires: pkgconfig(wayland-cursor) >= %{wayland_version}
BuildRequires: pkgconfig(wayland-egl) >= %{wayland_version}
BuildRequires: pkgconfig(wayland-protocols) >= %{wayland_protocols_version}
BuildRequires: pkgconfig(xi)
BuildRequires: pkgconfig(xrandr) >= %{xrandr_version}
BuildRequires: pkgconfig(xrender)
BuildRequires: pkgconfig(xcursor)
BuildRequires: pkgconfig(xfixes)
BuildRequires: pkgconfig(xinerama)
BuildRequires: pkgconfig(xcomposite)
BuildRequires: pkgconfig(xdamage)
BuildRequires: pkgconfig(xkbcommon)
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
BuildRequires: gettext
BuildRequires: gtk-doc
BuildRequires: meson

# standard icons
Requires: adwaita-icon-theme
# required for icon theme apis to work
Requires: hicolor-icon-theme
# split out in a subpackage
Requires: gtk-update-icon-cache

Requires: atk%{?_isa} >= %{atk_version}
Requires: cairo%{?_isa} >= %{cairo_version}
Requires: cairo-gobject%{?_isa} >= %{cairo_version}
Requires: glib2%{?_isa} >= %{glib2_version}
Requires: libepoxy%{?_isa} >= %{epoxy_version}
Requires: libwayland-client%{?_isa} >= %{wayland_version}
Requires: libwayland-cursor%{?_isa} >= %{wayland_version}
Requires: libXrandr%{?_isa} >= %{xrandr_version}
Requires: pango%{?_isa} >= %{pango_version}

# make sure we have a reasonable gsettings backend
Recommends: dconf%{?_isa}

# For sound theme events in gtk3 apps
Recommends: libcanberra-gtk3%{?_isa}

# For Tracker search in the file chooser.
Recommends: tracker-miners

Recommends: (ibus-gtk3 if ibus)

%description
GTK+ is a multi-platform toolkit for creating graphical user
interfaces. Offering a complete set of widgets, GTK+ is suitable for
projects ranging from small one-off tools to complete application
suites.

This package contains version 3 of GTK+.

%package -n gtk-update-icon-cache
Summary: Icon theme caching utility

%description -n gtk-update-icon-cache
GTK+ can use the cache files created by gtk-update-icon-cache to avoid a lot of
system call and disk seek overhead when the application starts. Since the
format of the cache files allows them to be mmap()ed shared between multiple
applications, the overall memory consumption is reduced as well.

%package immodules
Summary: Input methods for GTK+
Requires: gtk3%{?_isa} = %{version}-%{release}

%description immodules
The gtk3-immodules package contains standalone input methods that
are shipped as part of GTK+ 3.

%package immodule-xim
Summary: XIM support for GTK+
Requires: gtk3%{?_isa} = %{version}-%{release}

%description immodule-xim
The gtk3-immodule-xim package contains XIM support for GTK+ 3.

%package devel
Summary: Development files for GTK+
Requires: gtk3%{?_isa} = %{version}-%{release}

%description devel
This package contains the libraries and header files that are needed
for writing applications with version 3 of the GTK+ widget toolkit. If
you plan to develop applications with GTK+, consider installing the
gtk3-devel-docs package.

%package devel-docs
Summary: Developer documentation for GTK+
Requires: gtk3 = %{version}-%{release}

%description devel-docs
This package contains developer documentation for version 3 of the GTK+
widget toolkit.

%package tests
Summary: Tests for the %{name} package
Requires: %{name}%{?_isa} = %{version}-%{release}

%description tests
The %{name}-tests package contains tests that can be used to verify
the functionality of the installed %{name} package.

%prep
%autosetup -n gtk-%{version} -p1

%build
export CFLAGS='-fno-strict-aliasing %optflags'
%meson \
%if 0%{?with_broadway}
        -Dbroadway_backend=true \
%endif
        -Dbuiltin_immodules=wayland,waylandgtk \
        -Dcolord=yes \
%if 0%{?with_cloudproviders}
        -Dcloudproviders=true \
%endif
        -Dgtk_doc=true \
        -Dinstalled_tests=true \
        -Dman=true \
        -Dprofiler=true \
        -Dtracker3=true \
        -Dxinerama=yes \
%meson_build

%install
%meson_install

%find_lang gtk30
%find_lang gtk30-properties

(cd $RPM_BUILD_ROOT%{_bindir}
 mv gtk-query-immodules-3.0 gtk-query-immodules-3.0-%{__isa_bits}
)

echo ".so man1/gtk-query-immodules-3.0.1" > $RPM_BUILD_ROOT%{_mandir}/man1/gtk-query-immodules-3.0-%{__isa_bits}.1

touch $RPM_BUILD_ROOT%{_libdir}/gtk-3.0/%{bin_version}/immodules.cache

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/gtk-3.0
mkdir -p $RPM_BUILD_ROOT%{_libdir}/gtk-3.0/modules
mkdir -p $RPM_BUILD_ROOT%{_libdir}/gtk-3.0/immodules

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%transfiletriggerin -- %{_libdir}/gtk-3.0/3.0.0/immodules
gtk-query-immodules-3.0-%{__isa_bits} --update-cache &>/dev/null || :

%transfiletriggerpostun -- %{_libdir}/gtk-3.0/3.0.0/immodules
gtk-query-immodules-3.0-%{__isa_bits} --update-cache &>/dev/null || :

%files -f gtk30.lang
%license COPYING
%doc NEWS README.md
%{_bindir}/gtk-query-immodules-3.0*
%{_bindir}/gtk-launch
%{_libdir}/libgtk-3.so.0{,.*}
%{_libdir}/libgdk-3.so.0{,.*}
%{_libdir}/libgailutil-3.so.0{,.*}
%dir %{_libdir}/gtk-3.0
%dir %{_libdir}/gtk-3.0/%{bin_version}
%dir %{_libdir}/gtk-3.0/%{bin_version}/immodules
%{_libdir}/gtk-3.0/%{bin_version}/printbackends
%{_libdir}/gtk-3.0/modules
%{_libdir}/gtk-3.0/immodules
%{_datadir}/themes/Default
%{_datadir}/themes/Emacs
%{_libdir}/girepository-1.0
%ghost %{_libdir}/gtk-3.0/%{bin_version}/immodules.cache
%{_mandir}/man1/gtk-query-immodules-3.0*
%{_mandir}/man1/gtk-launch.1*
%{_datadir}/glib-2.0/schemas/org.gtk.Settings.ColorChooser.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gtk.Settings.Debug.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gtk.Settings.EmojiChooser.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gtk.Settings.FileChooser.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gtk.exampleapp.gschema.xml
%dir %{_datadir}/gtk-3.0
%{_datadir}/gtk-3.0/emoji/
%if 0%{?with_broadway}
%{_bindir}/broadwayd
%{_mandir}/man1/broadwayd.1*
%endif

%files -n gtk-update-icon-cache
%license COPYING
%{_bindir}/gtk-update-icon-cache
%{_mandir}/man1/gtk-update-icon-cache.1*

%files immodules
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-cedilla.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-am-et.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-cyrillic-translit.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-inuktitut.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-ipa.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-multipress.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-thai.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-ti-er.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-ti-et.so
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-viqr.so
%if 0%{?with_broadway}
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-broadway.so
%endif
%config(noreplace) %{_sysconfdir}/gtk-3.0/im-multipress.conf

%files immodule-xim
%{_libdir}/gtk-3.0/%{bin_version}/immodules/im-xim.so

%files devel -f gtk30-properties.lang
%{_libdir}/libgdk-3.so
%{_libdir}/libgtk-3.so
%{_libdir}/libgailutil-3.so
%{_includedir}/gail-3.0/
%{_includedir}/gtk-3.0/
%{_datadir}/aclocal/gtk-3.0.m4
%{_libdir}/pkgconfig/g*-3.0.pc
%{_bindir}/gtk3-demo
%{_bindir}/gtk3-icon-browser
%{_bindir}/gtk-builder-tool
%{_bindir}/gtk-encode-symbolic-svg
%{_bindir}/gtk-query-settings
%{_datadir}/applications/gtk3-demo.desktop
%{_datadir}/applications/gtk3-icon-browser.desktop
%{_datadir}/applications/gtk3-widget-factory.desktop
%{_datadir}/icons/hicolor/*/apps/gtk3-demo.png
%{_datadir}/icons/hicolor/*/apps/gtk3-demo-symbolic.symbolic.png
%{_datadir}/icons/hicolor/*/apps/gtk3-widget-factory.png
%{_datadir}/icons/hicolor/*/apps/gtk3-widget-factory-symbolic.symbolic.png
%{_bindir}/gtk3-demo-application
%{_bindir}/gtk3-widget-factory
%{_datadir}/gettext/
%{_datadir}/gir-1.0
%{_datadir}/glib-2.0/schemas/org.gtk.Demo.gschema.xml
%{_datadir}/gtk-3.0/gtkbuilder.rng
%{_datadir}/gtk-3.0/valgrind/
%{_mandir}/man1/gtk3-demo.1*
%{_mandir}/man1/gtk3-demo-application.1*
%{_mandir}/man1/gtk3-icon-browser.1*
%{_mandir}/man1/gtk3-widget-factory.1*
%{_mandir}/man1/gtk-builder-tool.1*
%{_mandir}/man1/gtk-encode-symbolic-svg.1*
%{_mandir}/man1/gtk-query-settings.1*

%files devel-docs
%{_datadir}/gtk-doc

%files tests
%{_libexecdir}/installed-tests/
%{_datadir}/installed-tests/

%changelog
%autochangelog
