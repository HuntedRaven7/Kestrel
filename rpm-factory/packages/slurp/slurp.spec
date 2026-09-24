Name:		slurp
Version:	1.5.0
Release:	7%{?dist}
Summary:	Select a region in Sway

License:	MIT
URL:		https://github.com/emersion/slurp
Source0:	%{url}/releases/download/v%{version}/slurp-%{version}.tar.gz
Source1:	%{url}/releases/download/v%{version}/slurp-%{version}.tar.gz.sig
Source2:	https://emersion.fr/.well-known/openpgpkey/hu/dj3498u4hyyarh35rkjfnghbjxug6b19

BuildRequires:	pkgconfig(wayland-client)
BuildRequires:	pkgconfig(wayland-cursor)
BuildRequires:	pkgconfig(wayland-protocols) >= 1.32
BuildRequires:	pkgconfig(cairo)
BuildRequires:	pkgconfig(xkbcommon)
BuildRequires:	scdoc
BuildRequires:	meson
BuildRequires:	gcc
BuildRequires:	gnupg2

%description
Slurp is a command-line tool that allows the user to visually select a region
and prints it to the standard output.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup

%build
%meson
%meson_build

%install
%meson_install

%files
%license LICENSE
%{_bindir}/slurp
%{_mandir}/man1/slurp.1*

%changelog
* Fri Jul 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Jan 19 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Sat Jul 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Sat Jan 27 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Dec 27 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.5.0-1
- Update to 1.5.0 (#2254537)

* Sat Jul 22 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sat Jan 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Sat Dec 10 2022 Benjamin Lowry <ben@ben.gmbh> - 1.4.0-1
- Slurp 1.4.0

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Sun Apr 18 2021 Benjamin Lowry <ben@ben.gmbh> - 1.3.2-1
- Slurp 1.3.2

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sun Nov 8 2020 Benjamin Lowry <ben@ben.gmbh> 1.3.1-1
- Slurp 1.3.1

* Fri Oct 16 2020 Benjamin Lowry <ben@ben.gmbh> 1.3.0-2
- fix silly dependency error

* Fri Oct 16 2020 Benjamin Lowry <ben@ben.gmbh> 1.3.0-1
- Slurp 1.3.0

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sun Mar 8 2020 Benjamin Lowry <ben@ben.gmbh> 1.2.0-3
- Update description

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Jan 10 2020 Benjamin Lowry <ben@ben.gmbh> 1.2.0-1
- Initial Fedora package
