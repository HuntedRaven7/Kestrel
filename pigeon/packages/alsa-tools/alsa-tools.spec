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
# sbiload lives under seq/ upstream; Fedora builds it from the top level
mv seq/sbiload . ; rm -rf seq
for d in %{builddirstools} %{builddirsfirmw}; do
  cd $d ; %configure
  make %{?_smp_mflags} || exit 1
  cd ..
done

%install
for d in %{builddirstools} %{builddirsfirmw}; do
  case $d in
    usx2yloader)
      (cd $d ; %make_install hotplugdir=/usr/lib/udev) || exit 1
      ;;
    *)
      (cd $d ; %make_install) || exit 1
      ;;
  esac
done

# udev rules for firmware loaders (vendored Source1)
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/udev/rules.d

# harvest per-tool READMEs/COPYINGs for %doc (each independently: most
# tools ship only one of the two)
for d in %{builddirstools} %{builddirsfirmw}; do
  if [[ -s "${d}"/README || -s "${d}"/COPYING ]]; then
    mkdir -p "%{buildroot}%{_pkgdocdir}/${d}"
    [[ -s "${d}"/README ]] && cp -a "${d}"/README "%{buildroot}%{_pkgdocdir}/${d}/"
    [[ -s "${d}"/COPYING ]] && cp -a "${d}"/COPYING "%{buildroot}%{_pkgdocdir}/${d}/"
  fi
done

# usx2yloader installs a legacy hotplug usermap; udev rules cover it
rm -f %{buildroot}/usr/lib/udev/tascam_fw.usermap

%files
%dir %{_pkgdocdir}
%doc %{_pkgdocdir}/as10k1
%doc %{_pkgdocdir}/echomixer
%doc %{_pkgdocdir}/envy24control
%doc %{_pkgdocdir}/hdspconf
%doc %{_pkgdocdir}/hdspmixer
%doc %{_pkgdocdir}/hwmixvolume
%doc %{_pkgdocdir}/rmedigicontrol
%doc %{_pkgdocdir}/sbiload
%doc %{_pkgdocdir}/hda-verb
%doc %{_pkgdocdir}/hdajackretask
%license %{_pkgdocdir}/as10k1/COPYING
%{_bindir}/as10k1
%{_bindir}/echomixer
%{_bindir}/envy24control
%{_bindir}/hdspconf
%{_bindir}/hdspmixer
%{_bindir}/hwmixvolume
%{_bindir}/rmedigicontrol
%{_bindir}/sbiload
%{_bindir}/sscape_ctl
%{_bindir}/us428control
%{_bindir}/hda-verb
%{_bindir}/hdajackretask
%{_bindir}/hdajacksensetest
%{_datadir}/sounds/*
%{_datadir}/man/man1/envy24control.1.gz
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png

# sb16_csp stuff which is excluded for PPC
%ifnarch ppc ppc64
%doc %{_pkgdocdir}/sb16_csp
%{_bindir}/cspctl
%{_datadir}/man/man1/cspctl.1.gz
%endif

%files firmware
%dir %{_pkgdocdir}
%doc %{_pkgdocdir}/hdsploader
%doc %{_pkgdocdir}/mixartloader
%doc %{_pkgdocdir}/usx2yloader
%doc %{_pkgdocdir}/vxloader
%license %{_pkgdocdir}/hdsploader/COPYING
%{_bindir}/hdsploader
%{_bindir}/mixartloader
%{_bindir}/usx2yloader
%{_bindir}/vxloader
/usr/lib/udev/tascam_fpga
/usr/lib/udev/tascam_fw
%config(noreplace) %{_sysconfdir}/udev/rules.d/90-alsa-tools-firmware.rules

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.2.15-5.hum1.pigeon
- Initial Kestrel package (independent recipe)