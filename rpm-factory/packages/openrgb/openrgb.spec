%global forgeurl https://gitlab.com/CalcProgrammer1/OpenRGB
%global commit 74cbdcce55711f57b3ca4439d3136f5bb7068db7
#%%global tag release_%%{version}
# Workaround for incorrect package suffix name with forge macros
# (.20231017gitrelease.0.9 for example)
#%%global distprefix %%{nil}

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch: %{ix86}

Name:           openrgb
Version:        1.0~rc2
%forgemeta
Release:        %autorelease
Summary:        Open source RGB lighting control

# Entire source code is GPL-2.0-only except some bundled libs:
#   * GPL-3.0-or-later:
#     - hueplusplus-1.0.0
#     - libcmmk
License:        GPL-2.0-only AND GPL-3.0-or-later
URL:            https://openrgb.org
Source:         %{forgesource}

BuildRequires:  desktop-file-utils
BuildRequires:  gcc-c++
BuildRequires:  libappstream-glib
BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(hidapi-libusb)
BuildRequires:  pkgconfig(libusb)
BuildRequires:  pkgconfig(mbedtls)
BuildRequires:  cmake
BuildRequires:  cmake(Qt5)
BuildRequires:  cmake(Qt5LinguistTools)
Requires:       %{name}-udev-rules = %{version}-%{release}
Requires:       hicolor-icon-theme
Provides:       bundled(hueplusplus) = 1.2.0
Provides:       bundled(libcmmk)

%description
One of the biggest complaints about RGB is the software ecosystem surrounding
it.  Every manufacturer has their own app, their own brand, their own style.  If
you want to mix and match devices, you end up with a ton of conflicting,
functionally identical apps competing for your background resources.  On top of
that, these apps are proprietary and Windows-only.  Some even require online
accounts.  What if there was a way to control all of your RGB devices from a
single app, on Windows, Linux, and MacOS, without any nonsense?  That is what
OpenRGB sets out to achieve.  One app to rule them all.


# Separate Udev rules package is useful for Flatpak package and others
%package        udev-rules
Summary:        Udev rules for %{name}
BuildArch:      noarch

Requires:       systemd-udev
Suggests:       %{name} = %{version}-%{release}

%description    udev-rules
Udev rules for %{name}.


%prep
%forgeautosetup -p1

# Remove some bundled libs
pushd dependencies
rm -rf       \
  hidapi     \
  hidapi-win \
  libusb-*   \
  mbedtls-*  \
  %{nil}
popd


%build
%qmake_qt5 \
    .      \
    %{nil}
%make_build


%install
%make_install INSTALL_ROOT=%{buildroot}


%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.xml
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop


# Need to manually reload udev rules to get working app right after installing
# package
%post -n %{name}-udev-rules
if [ -S /run/udev/control ]; then
    udevadm control --reload
    udevadm trigger
fi


%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service


%files
%doc README.md
%{_bindir}/%{name}
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png
%{_metainfodir}/*.metainfo.xml
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/*.service


%files udev-rules
%license LICENSE
%{_udevrulesdir}/60-%{name}.rules


%changelog
%autochangelog
