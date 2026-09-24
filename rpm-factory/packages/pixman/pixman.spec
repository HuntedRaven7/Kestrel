%define gitdate 20070827
%define gitrev 8ff7213f39edc1b2b8b60d6b0cc5d5f14ca1928d

Name:           pixman
Version:        0.46.4
Release:        %autorelease
Summary:        Pixel manipulation library

# SPDX
License:        MIT
URL:            https://gitlab.freedesktop.org/pixman/pixman
#VCS:           git:git://git.freedesktop.org/git/pixman
# To make git snapshots:
# ./make-pixman-snapshot.sh %{\?gitrev}
# if no revision specified, makes a new one from HEAD.
Source0:        https://xorg.freedesktop.org/archive/individual/lib/%{name}-%{version}.tar.xz
Source1:        make-pixman-snapshot.sh

BuildRequires:  gcc
BuildRequires:  meson

%description
Pixman is a pixel manipulation library for X and Cairo.

%package devel
Summary: Pixel manipulation library development package
Requires: %{name}%{?isa} = %{version}-%{release}
Requires: pkgconfig

%description devel
Pixel manipulation library for X and Cairo development package.

%prep
%autosetup -p1

%build
%meson --auto-features=auto \
  %nil

%meson_build

%install
%meson_install

%check
%meson_test

%ldconfig_post
%ldconfig_postun

%files
%doc COPYING
%{_libdir}/libpixman-1*.so.*

%files devel
%dir %{_includedir}/pixman-1
%{_includedir}/pixman-1/pixman.h
%{_includedir}/pixman-1/pixman-version.h
%{_libdir}/libpixman-1*.so
%{_libdir}/pkgconfig/pixman-1.pc

%changelog
%autochangelog
