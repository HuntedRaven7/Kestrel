# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: http://www.alsa-project.org/ (version 1.2.15).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

# If you want to skip building the firmware subpackage, define the macro
# _without_firmware to 1. This is not the actual firmware itself 
# (see alsa-firmware), it is some complementary tools.
# Do *NOT* set it to zero or have a commented out define here, or it will not
# work. (RPM spec file voodoo)
%if 0%{?rhel}
%global _without_tools 1
%endif

%ifarch ppc ppc64
# sb16_csp doesn't build on PPC; see bug #219010
%{?!_without_tools:     %global builddirstools as10k1 echomixer envy24control hdspconf hdspmixer hwmixvolume rmedigicontrol sbiload sscape_ctl us428control hda-verb hdajackretask hdajacksensetest }
%else
%{?!_without_tools:     %global builddirstools as10k1 echomixer envy24control hdspconf hdspmixer hwmixvolume rmedigicontrol sbiload sb16_csp sscape_ctl us428control hda-verb hdajackretask hdajacksensetest }
%endif

%{?!_without_firmware:  %global builddirsfirmw hdsploader mixartloader usx2yloader vxloader }

%{?!_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}

# Note that the Version is intended to coincide with the version of ALSA
# included with the Fedora kernel, rather than necessarily the very latest
# upstream version of alsa-tools

Summary:        Specialist tools for ALSA
Name:           alsa-tools
Version:        1.2.15
Release:        5.hum1.pigeon
License:        GPL-2.0-or-later
URL:            http://www.alsa-project.org/
Source:         ftp://ftp.alsa-project.org/pub/tools/%{name}-%{version}.tar.bz2

Source1:        90-alsa-tools-firmware.rules

Patch1:         hwmixvolume-python.patch

BuildRequires:  gcc gcc-c++
BuildRequires:  alsa-lib-devel >= %{version}
%if 0%{?_without_tools} == 0
BuildRequires:  gtk2-devel
BuildRequires:  gtk3-devel
BuildRequires:  gtk4-devel
BuildRequires:  fltk-devel
BuildRequires: make
BuildRequires:  desktop-file-utils
Requires:       xorg-x11-fonts-misc
# Needed for hwmixvolume
Requires:       python3-alsa
%endif

%description
This package contains several specialist tools for use with ALSA, including
a number of programs that provide access to special hardware facilities on
certain sound cards.

* as10k1 - AS10k1 Assembler
%ifnarch ppc ppc64
* cspctl - Sound Blaster 16 ASP/CSP control program
%endif
* echomixer - Mixer for Echo Audio (indigo) devices
* envy24control - Control tool for Envy24 (ice1712) based soundcards
* hdspmixer - Mixer for the RME Hammerfall DSP cards
* hwmixvolume - Control the volume of individual streams on sound cards that
  use hardware mixing
* rmedigicontrol - Control panel for RME Hammerfall cards
* sbiload - An OPL2/3 FM instrument loader for ALSA sequencer
* sscape_ctl - ALSA SoundScape control utility
* us428control - Control tool for Tascam 428
* hda-verb - Direct HDA codec access
* hdajackretask - Reassign the I/O jacks on the HDA hardware
* hdajacksensetest - The sense test for the I/O jacks on the HDA hardware


%package firmware
Summary:        ALSA tools for uploading firmware to some soundcards
Requires:       udev
Requires:       alsa-firmware

%description firmware
This package contains tools for uploading firmware to sound cards.

%prep
%autosetup -p1

%build
%if "%{builddirstools}" != ""
for d in %{builddirstools}; do
  make -C $d
done
%endif

%if "%{builddirsfirmw}" != ""
for d in %{builddirsfirmw}; do
  make -C $d
done
%endif

%install
%if "%{builddirstools}" != ""
for d in %{builddirstools}; do
  make -C $d DESTDIR=%{buildroot} install
done
%endif

%if "%{builddirsfirmw}" != ""
for d in %{builddirsfirmw}; do
  make -C $d DESTDIR=%{buildroot} install
done
%endif

%files
%doc TODO
%license COPYING
%{_bindir}/*
%{_datadir}/alsa-tools/
%{_datadir}/applications/*alsa-tools*.desktop
%{_datadir}/icons/hicolor/*/apps/*alsa-tools*.png

%files firmware
%doc TODO
%license COPYING
%{_libdir}/alsa-tools/
%{_datadir}/alsa-tools/firmware/
%config(noreplace) %{_sysconfdir}/udev/rules.d/90-alsa-tools-firmware.rules

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.2.15-5.hum1.pigeon
- Initial Kestrel package (independent recipe)