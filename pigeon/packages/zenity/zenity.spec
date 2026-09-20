Name:          zenity
Version:       4.2.2
Release:       %autorelease
Summary:       Display dialog boxes from shell scripts

License:       LGPL-2.1-or-later
URL:           https://wiki.gnome.org/Projects/Zenity
Source:        https://download.gnome.org/sources/%{name}/%{gnome_major_minor_version}/%{name}-%{version}.tar.xz

BuildRequires: pkgconfig(libadwaita-1) >= 1.2
BuildRequires: /usr/bin/help2man
BuildRequires: desktop-file-utils
BuildRequires: gcc
BuildRequires: gettext
BuildRequires: itstool
BuildRequires: meson
BuildRequires: which
# Tests
BuildRequires: xwayland-run
BuildRequires: mutter
BuildRequires: mesa-dri-drivers
BuildRequires: mesa-libEGL

%description
Zenity lets you display Gtk+ dialog boxes from the command line and through
shell scripts. It is similar to gdialog, but is intended to be saner. It comes
from the same family as dialog, Xdialog, and cdialog.

%prep
%autosetup -p1


%build
%meson
# Man page generation requires running the in-tree zenity command.
%{shrink:xwfb-run -c mutter -w 10 -- %meson_build}


%install
%meson_install

# we don't want a perl dependency just for this
rm -f %{buildroot}/%{_bindir}/gdialog

%find_lang zenity --with-gnome

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/org.gnome.Zenity.desktop


%files -f zenity.lang
%license COPYING
%doc AUTHORS NEWS README.md
%{_bindir}/zenity
%{_datadir}/applications/org.gnome.Zenity.desktop
%{_datadir}/icons/hicolor/48*48/apps/zenity.png
%{_mandir}/man1/zenity.1*


%changelog
%autochangelog
