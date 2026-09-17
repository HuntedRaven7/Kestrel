%global udevdir %(pkg-config --variable=udevdir udev)

Name:           libratbag
Version:        0.18
Release:        6%{?gitdate:.%{gitdate}git%{gitversion}}%{?dist}
Summary:        Programmable input device library
License:        MIT
URL:            https://github.com/libratbag/libratbag
Source0:        https://github.com/libratbag/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

# 0.18+ now installs into /usr/sbin, let's revert that
# for now until sure that's a permanent change
# https://github.com/libratbag/libratbag/issues/1672
Patch0001:      0001-Revert-build-install-ratbagd-into-sbindir.patch

BuildRequires:  git gcc gcc-c++
BuildRequires:  meson pkgconfig
BuildRequires:  libevdev-devel
BuildRequires:  libudev-devel
BuildRequires:  pkgconfig(udev) pkgconfig(glib-2.0) pkgconfig(json-glib-1.0)
BuildRequires:  check-devel
%ifarch %{valgrind_arches}
BuildRequires:  valgrind
%endif
BuildRequires:  systemd
BuildRequires:  python3 python3-devel python3-gobject
BuildRequires:  python3-lxml python3-evdev swig
BuildRequires:  libunistring-devel

%description
libratbag is a library that allows to configure programmable
mice.

%package        ratbagd
Summary:        DBus daemon to access programmable input devices
Obsoletes:      libratbag < 0.9.900
Requires:       python3-evdev python3-gobject

%description    ratbagd
The ratbagd package contains a dbus daemon to access and configure
programmable input devices, primarily gaming mice.

%package        -n liblur
Summary:        Logitech Unifying Receiver library

%description    -n liblur
The liblur package contains libraries and tools to access and
configure the Logitech Unifying Receivers. The functionality
are mainly listing, pairing and un-pairing Logitech devices
attached to a receiver.

%package        -n liblur-devel
Summary:        Development files for liblur
Requires:       liblur%{?_isa} = %{version}-%{release}

%description    -n liblur-devel
The liblur-devel package contains libraries and header files for
developing applications that use liblur.

%prep
%autosetup -S git

# hack until rhbz#1409661 gets fixed
%{!?__global_cxxflags: %define __global_cxxflags %{optflags}}

%build
# s390x builds sometimes fails during the tests, let just disable those
%ifarch s390x
%meson -Dudev-dir=%{udevdir} -Ddocumentation=false -Dtests=false
%else
%meson -Dudev-dir=%{udevdir} -Ddocumentation=false
%endif
%meson_build

%check
%meson_test

%install
%meson_install


%ldconfig_scriptlets -n liblur

%files ratbagd
%license COPYING
%{_bindir}/ratbagctl
%{_bindir}/ratbagd
%dir %{_datadir}/libratbag
%{_datadir}/libratbag/*.device
%{_mandir}/man1/ratbagctl.1*
%{_mandir}/man8/ratbagd.8*
%{_datadir}/dbus-1/system.d/org.freedesktop.ratbag1.conf
%{_datadir}/dbus-1/system-services/org.freedesktop.ratbag1.service
%{_unitdir}/ratbagd.service

%files -n liblur
%license COPYING
%{_libdir}/liblur.so.*
%{_bindir}/lur-command
%{_mandir}/man1/lur-command.1*

%files -n liblur-devel
%{_includedir}/liblur.h
%{_libdir}/liblur.so
%{_libdir}/pkgconfig/liblur.pc

%changelog
* Thu Jul 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.18-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.18-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.18-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Thu Mar 06 2025 David Abdurachmanov <davidlt@rivosinc.com> 0.18-3
- Properly check valgrind arches

* Mon Jan 20 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.18-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Fri Jan 03 2025 Peter Hutterer <peter.hutterer@redhat.com> - 0.18-1
- libratbag 0.18
- Revert upstream change to /sbin

* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.17-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Wed Jun 26 2024 Marcin Juszkiewicz <marcin@juszkiewicz.com.pl> - 0.17-6
- Backport remove of imp Python module to fix FTFBS on F40.

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.17-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.17-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Sep 08 2023 Peter Hutterer <peter.hutterer@redhat.com>
- SPDX migration: license is MIT, we're good

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.17-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.17-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Nov 30 2022 Peter Hutterer <peter.hutterer@redhat.com> - 0.17-1
- libratbag 0.17

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.16-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.16-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Thu Jul 22 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.16-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Fri Jun 25 2021 Peter Hutterer <peter.hutterer@redhat.com> 0.16-1
- libratbag 0.16

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.15-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Sep 28 2020 Peter Hutterer <peter.hutterer@redhat.com> 0.15-1
- libratbag 0.15

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.14-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Thu May 21 2020 Peter Hutterer <peter.hutterer@redhat.com> 0.14-1
- libratbag 0.14

* Tue Feb 11 2020 Peter Hutterer <peter.hutterer@redhat.com> 0.13-1
- libratbag 0.13

* Wed Jan 29 2020 Peter Hutterer <peter.hutterer@redhat.com> 0.12-1
- libratbag 0.12

* Tue Nov 05 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.11-1
- libratbag 0.11

* Mon Sep 16 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.10-2
- Add missing Requires for ratbagctl

* Fri Aug 02 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.10-1
- libratbag 0.10

* Fri Jul 26 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.9.906-1
- libratbag 0.9.906

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.9.905-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Jul 17 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.9.905-3
- Use python3-embed as dependency where available. Fixes FTBFS with python
  3.8 (#1718290)

* Thu Feb 28 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.9.905-2
- Fix meson options

* Thu Feb 28 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.9.905-1
- libratbag 0.9.905

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.9.904-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Jan 24 2019 Peter Hutterer <peter.hutterer@redhat.com> 0.9.904-1
- libratbag 0.9.904

* Wed Sep 05 2018 Peter Hutterer <peter.hutterer@redhat.com> 0.9.903-1
- libratbag 0.9.903

* Fri Jul 20 2018 Peter Hutterer <peter.hutterer@redhat.com> 0.9.902-4
- Add gcc to BuildRequires (#1604654)
- Change to use the correct -Ddocumentation=false

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.9.902-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.9.902-2
- Rebuilt for Python 3.7

* Mon May 21 2018 Peter Hutterer <peter.hutterer@redhat.com> 0.9.902-1
- libratbag 0.9.902

* Fri Mar 23 2018 Peter Hutterer <peter.hutterer@redhat.com> 0.9.901-1
- libratbag 0.9.901

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.9-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.9-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Wed Jun 07 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.9-2
- disable tests on s390x because they seem to fail without good reasons

* Tue Jun 06 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.9-1
- libratbag v0.9
- new manpage for lur-command

* Tue May 09 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.8-1
- libratbag v0.8

* Tue May 09 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.7-3
- add a hack for F24 and F25 to compile

* Fri May 05 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.7-2
- Remove the generation of the documentation, we don't ship it

* Thu May 04 2017 Benjamin Tissoires <benjamin.tissoires@redhat.com> 0.7-1
- Initial Fedora packaging (rhbz#1309703)
