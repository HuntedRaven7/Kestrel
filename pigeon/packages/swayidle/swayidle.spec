Name: swayidle
Version: 1.9.0
Release: 3%{?dist}
Summary: An idle daemon for wayland compositors

# Automatically converted from old format: MIT and LGPLv2+ - review is highly recommended.
License: LicenseRef-Callaway-MIT AND LicenseRef-Callaway-LGPLv2+
URL: https://github.com/swaywm/swayidle
Source0: %{url}/releases/download/%{version}/%{name}-%{version}.tar.gz
Source1: %{url}/releases/download/%{version}/%{name}-%{version}.tar.gz.sig
# 0FDE7BE0E88F5E48: emersion <contact@emersion.fr>
Source2: https://emersion.fr/.well-known/openpgpkey/hu/dj3498u4hyyarh35rkjfnghbjxug6b19#/gpgkey-0FDE7BE0E88F5E48.gpg

BuildRequires: meson >= 0.59.0
BuildRequires: gcc
BuildRequires: gnupg2
BuildRequires: pkgconfig(wayland-protocols) >= 1.40
BuildRequires: pkgconfig(wayland-client)
BuildRequires: pkgconfig(wayland-server)
BuildRequires: pkgconfig(libsystemd)
BuildRequires: scdoc

%description
swayidle is an idle management daemon for Wayland compositors.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup -p1

%build
%meson
%meson_build

%install
%meson_install

%check
%meson_test

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_datadir}/bash-completion/completions/%{name}
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/fish/vendor_completions.d/swayidle.fish
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{_datadir}/zsh/site-functions/_%{name}
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{_mandir}/man1/%{name}.1.gz

%changelog
* Fri Jul 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Nov 06 2025 Jack Hildebrandt <jack@jackhil.de> - 1.9.0-1
- Update to 1.9.0

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Jan 19 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Wed Sep 04 2024 Miroslav Suchý <msuchy@redhat.com> - 1.8.0-6
- convert license to SPDX

* Sat Jul 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Sat Jan 27 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Jul 22 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sat Jan 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Sun Dec 04 2022 Jack Hildebrandt <jack@jackhil.de> - 1.8.0-1
- Update to 1.8.0 (#f554943)
- Remove 32-bit patch that's included in new version

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Sat Feb 05 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.7.1-1
- Update to 1.7.1 (#2041188)
- Add source verification
- Apply upstream patch to fix build on 32-bit architectures

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Thu Aug 19 2021 Jack Hildebrandt <jack@jackhil.de> - 1.7-1
- Update to 1.7

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Jan 23 2020 Jack Hildebrandt <jack@jackhil.de> - 1.6-1
- Update to 1.6

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Jul 11 2019 Jack Hildebrandt <jack@jackhil.de> - 1.5-1
- Update to 1.5. (1.4 is the same)

* Sun May 05 2019 Jack Hildebrandt <jack@jackhil.de> - 1.3-1
- Update to 1.3

* Sun Apr 07 2019 Jack Hildebrandt <jack@jackhil.de> - 1.2-5
- Add patch for "control reaches end of non-void function" error

* Wed Mar 20 2019 Jack Hildebradnt <jack@jackhil.de> - 1.2-4
- Fix license tag

* Mon Mar 18 2019 Jack Hildebrandt <jack@jackhil.de> - 1.2-3
- Flip changelog

* Fri Mar 15 2019 Jack Hildebrandt <jack@jackhil.de> - 1.2-2
- Fix directory ownership
- Clean up spec file

* Fri Mar 15 2019 Jack Hildebrandt <jack@jackhil.de> - 1.2-1
- Initial packaging

