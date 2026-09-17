%global foot_terminfo foot-extra
%global default_terminfo foot
%global fcft_minver 3.3.1

Name:           foot
Version:        1.28.0
Release:        1%{?dist}
Summary:        Fast, lightweight and minimalistic Wayland terminal emulator

# Main package license: MIT
# icons/hicolor/scalable/apps/foot.svg: CC-BY-SA-4.0
License:        MIT AND CC-BY-SA-4.0
URL:            https://codeberg.org/dnkl/%{name}
Source0:        %{url}/releases/download/%{version}/%{name}-%{version}.tar.gz
Source1:        %{url}/releases/download/%{version}/%{name}-%{version}.tar.gz.sig
# Daniel Eklöf (Git signing) <daniel@ekloef.se>
Source2:        gpgkey-5BBD4992C116573F.asc
Source3:        org.codeberg.dnkl.foot.metainfo.xml

BuildRequires:  gcc
BuildRequires:  gpgverify
BuildRequires:  meson >= 0.59.0
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  python3
BuildRequires:  systemd-rpm-macros

BuildRequires:  libutempter
BuildRequires:  pkgconfig(fcft) >= %{fcft_minver}
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(libutf8proc)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(scdoc)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(tllist) >= 1.1.0
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-cursor)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.41
BuildRequires:  pkgconfig(wayland-scanner) 
BuildRequires:  pkgconfig(xkbcommon)
# require *-static for header-only library
BuildRequires:  tllist-static

Requires:       fcft%{?_isa} >= %{fcft_minver}

Recommends:     ncurses-base
Requires:       (ncurses-base >= 6.4-5.20230520 if ncurses-base)
# require matching version of foot-terminfo if installed
Requires:       (%{name}-terminfo = %{version}-%{release} if %{name}-terminfo)

# Optional dependency for bell = notify option
Recommends:     /usr/bin/notify-send
# Optional dependency for opening URLs
Recommends:     /usr/bin/xdg-open
Requires:       hicolor-icon-theme

%description
Fast, lightweight and minimalistic Wayland terminal emulator.
Features:
 * Fast
 * Lightweight, in dependencies, on-disk and in-memory
 * Wayland native
 * DE agnostic
 * Server/daemon mode
 * User configurable font fallback
 * On-the-fly font resize
 * On-the-fly DPI font size adjustment
 * Scrollback search
 * Keyboard driven URL detection
 * Color emoji support
 * IME (via text-input-v3)
 * Multi-seat
 * Synchronized Updates support
 * Sixel image support

%package        terminfo
Summary:        Terminfo files for %{name} terminal
BuildRequires:  /usr/bin/tic
Requires:       ncurses-base

%description    terminfo
%{summary}.


%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup -p1


%build
%meson \
    -Dterminfo-base-name=%{foot_terminfo} \
    -Ddefault-terminfo=%{default_terminfo}
%meson_build


%install
%meson_install
install -D -pv -m0644 %{SOURCE3} \
    %{buildroot}%{_metainfodir}/org.codeberg.dnkl.foot.metainfo.xml
# Will be installed to correct location with rpm macros
rm %{buildroot}%{_docdir}/%{name}/LICENSE


%check
%meson_test
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.metainfo.xml
desktop-file-validate \
    %{buildroot}/%{_datadir}/applications/%{name}*.desktop


%post
%systemd_user_post %{name}-server.{service,socket}

%preun
%systemd_user_preun %{name}-server.{service,socket}


%files
%license LICENSE
%dir %{_sysconfdir}/xdg/%{name}
%config(noreplace) %{_sysconfdir}/xdg/%{name}/%{name}.ini
%{_bindir}/%{name}
%{_bindir}/%{name}client
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}*.desktop
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_metainfodir}/org.codeberg.dnkl.foot.metainfo.xml
%{bash_completions_dir}/foot*
%{fish_completions_dir}/foot*
%{zsh_completions_dir}/_foot*
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/CHANGELOG.md
%doc %{_docdir}/%{name}/README.md
%{_mandir}/man1/%{name}.1*
%{_mandir}/man1/%{name}client.1*
%{_mandir}/man5/%{name}.ini.5*
%{_mandir}/man7/%{name}-ctlseqs.7*
%{_userunitdir}/%{name}-server.service
%{_userunitdir}/%{name}-server.socket

%files terminfo
%license LICENSE
%dir %{_datadir}/terminfo/f
%{_datadir}/terminfo/f/%{foot_terminfo}
%{_datadir}/terminfo/f/%{foot_terminfo}-direct


%changelog
* Wed Sep 02 2026 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.28.0-1
- Update to 1.28.0 (#2527360)

* Wed Jul 15 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.27.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Sat May 16 2026 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.27.0-1
- Update to 1.27.0 (#2447592)

* Sat Mar 07 2026 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.26.0-1
- Update to 1.26.0 (#2444132)

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.25.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Oct 16 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.25.0-1
- Update to 1.25.0 (#2404359)

* Sun Sep 14 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.24.0-1
- Update to 1.24.0 (#2394766)

* Wed Jul 23 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.23.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Wed Jul 23 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.23.1-1
- Update to 1.23.1 (#2382804)

* Sat Jul 19 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.23.0-1
- Update to 1.23.0 (#2380423)

* Thu May 01 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.22.3-1
- Update to 1.22.3 (#2363239)

* Wed Apr 30 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.22.2-1
- Update to 1.22.2 (#2363052)

* Sat Apr 26 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.22.1-1
- Update to 1.22.1 (#2362436)

* Thu Apr 17 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.22.0-1
- Update to 1.22.0 (#2360691)

* Mon Mar 17 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.21.0-1
- Update to 1.21.0 (#2352903)

* Sun Jan 19 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.20.2-1
- Update to 1.20.2 (#2338726)

* Thu Jan 16 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.20.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Fri Jan 03 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.20.1-1
- Update to 1.20.1 (#2335391)

* Wed Jan 01 2025 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.20.0-1
- Update to 1.20.0 (#2335133)

* Thu Oct 24 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.19.0-1
- Update to 1.19.0 (#2321289)

* Tue Oct 08 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.18.1-2
- Rebuilt for utf8proc 2.9.0

* Thu Aug 15 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.18.1-1
- Update to 1.18.1 (#2304836)

* Sat Aug 03 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.18.0-1
- Update to 1.18.0 (#2302508)

* Wed Jul 17 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.17.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Wed Apr 17 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.17.2-1
- Update to 1.17.2 (#2275462)

* Sat Apr 13 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.17.1-1
- Update to 1.17.1 (#2274532)

* Sat Apr 06 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.17.0-1
- Update to 1.17.0 (#2244671)
- Convert License tag to SPDX
- Verify source signature

* Wed Jan 24 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.16.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.16.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Oct 14 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.16.1-1
- Update to 1.16.1 (#2243307)

* Tue Aug 08 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.15.3-1
- Update to 1.15.3 (#2229756)

* Sun Jul 30 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.15.2-1
- Update to 1.15.2 (#2227522)

* Sat Jul 22 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.15.1-1
- Update to 1.15.1 (#2224500)

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.15.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Fri Jul 14 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.15.0-1
- Update to 1.15.0 (#2222891)

* Thu Jun 29 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.14.0-3
- Rename terminfo entries to 'foot-extra'/'foot-extra-direct' (rhbz#2217996)
- Use 'foot' terminfo entry from ncurses-base by default on f39+

* Sat Apr 29 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.14.0-2
- Use correct dock and window switcher icons in GNOME

* Tue Apr 04 2023 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.14.0-1
- Update to 1.14.0 (#2184129)
- Install AppStream metadata
- Use new macros for shell completion directories

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.13.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Aug 31 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.13.1-1
- Update to 1.13.1 (#2123078)

* Sun Aug 07 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.13.0-1
- Update to 1.13.0

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.12.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Thu Apr 28 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.12.1-1
- Update to 1.12.1 (#2079544)

* Fri Apr 22 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.12.0-1
- Update to 1.12.0 (#2077953)
- Example config was moved to /etc/xdg/foot/foot.ini (upstream change)
- Install systemd unit files for foot --server

* Sat Feb 05 2022 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.11.0-1
- Update to 1.11.0 (#2051005)

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.10.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Wed Dec 08 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.10.3-1
- Update to 1.10.3 (#2030411)

* Fri Dec 03 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.10.2-1
- Update to 1.10.2

* Mon Nov 22 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.10.1-1
- Update to 1.10.1 (#2025735)

* Sun Nov 14 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.10.0-1
- Update to 1.10.0 (#2009965)

* Fri Oct 01 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.9.1-1
- Update to 1.9.1

* Fri Aug 27 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.9.0-1
- Update to 1.9.0
- Override custom terminfo dir with /usr/share/terminfo

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jul 20 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.8.2-2
- Add runtime dependency on fcft 2.4

* Sun Jul 18 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.8.2-1
- Update to 1.8.2

* Fri Jul 02 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.8.1-1
- Update to 1.8.1

* Fri Jun 25 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.8.0-1
- Update to 1.8.0

* Sun Apr 18 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.7.2-1
- Update to 1.7.2

* Sun Mar 28 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.7.1-1
- Update to 1.7.1

* Sat Mar 20 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.7.0-1
- Update to 1.7.0

* Wed Mar 10 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 1.6.4-1
- Initial import (#1912856)
