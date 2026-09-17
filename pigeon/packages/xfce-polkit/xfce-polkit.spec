Name:           xfce-polkit
Version:        0.3
Release:        18%{?dist}
Summary:        Simple PolicyKit authentication agent for Xfce

# Automatically converted from old format: GPLv2+ - review is highly recommended.
License:        GPL-2.0-or-later
URL:            https://github.com/ncopa/%{name}
Source0:        %{url}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires: make
BuildRequires:  gcc
BuildRequires:  automake
BuildRequires:  libxfce4ui-devel polkit-devel
BuildRequires:  desktop-file-utils

Provides: PolicyKit-authentication-agent

Requires: polkit >= 0.97

%description
%{summary}.


%prep
%autosetup
autoreconf -fi

%build
%configure
%make_build

%install
%make_install
desktop-file-edit --remove-key=NotShowIn --add-only-show-in=XFCE \
 %{buildroot}%{_sysconfdir}/xdg/autostart/%{name}.desktop

%files
%license LICENSE
%doc AUTHORS README.md
# do not distribute empty documentation files
#doc ChangeLog NEWS
%{_sysconfdir}/xdg/autostart/xfce-polkit.desktop
%{_libexecdir}/%{name}

%changelog
* Fri Jul 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-18
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Jan 19 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Fri Jul 26 2024 Miroslav Suchý <msuchy@redhat.com> - 0.3-14
- convert license to SPDX

* Sat Jul 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Sat Jan 27 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Jul 22 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sat Jan 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Sun Nov 11 2018 Kevin Fenzi <kevin@scrye.com> - 0.3-1
- Update to 0.3. Drop autostart conditionals.

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jul 07 2016 Raphael Groner <projects.rg@smart.ms> - 0.2-8
- autostart in xfce only, rhbz#1350775
- use autoreconf

* Sat Jun 18 2016 Raphael Groner <projects.rg@smart.ms> - 0.2-7
- enable autostart in epel7, rhbz#1343772

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Dec 21 2015 Raphael Groner <projects.rg@smart.ms> - 0.2-5
- add build conditional for inclusion of desktop file for autostart
  (rhbz#1281464)

* Sat Dec 19 2015 Raphael Groner <projects.rg@smart.ms> - 0.2-4
- disable desktop file in Fedora 23 and prior (in favor of gnome-polkit)

* Sat Dec 19 2015 Raphael Groner <projects.rg@smart.ms> - 0.2-3
- show name in xfce4-session, rhbz#1281464

* Sun Nov 08 2015 Kevin Fenzi <kevin@scrye.com> - 0.2-2
- Enable desktop file.

* Sat Sep 26 2015 Raphael Groner <projects.rg@smart.ms> - 0.2-1
- new version 0.2, rhbz#1266689
- disable default autostart for now to avoid conflict with xfce4-session

* Sat Sep 26 2015 Raphael Groner <projects.rg@smart.ms> - 0.1-1
- official upstream version 0.1

* Sat Sep 26 2015 Raphael Groner <projects.rg@smart.ms> - 0-0.2.20150924git05568a1
- fix segfault with glib-2.45 (upstream), rhbz#1264590

* Mon Jul 27 2015 Raphael Groner <projects.rg@smart.ms> - 0-0.1.20130717gitbe888ee
- initial
