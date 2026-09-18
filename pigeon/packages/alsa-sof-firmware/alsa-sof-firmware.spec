# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/thesofproject/sof-bin (tag v2025.12.2).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

# This is a firmware package, so binaries (which are not run on the host)
# in the end package are expected.
%define _binaries_in_noarch_packages_terminate_build   0
%global _firmwarepath  /usr/lib/firmware
%global _xz_opts -9 --check=crc32

%global sof_ver 2025.12.2
#global sof_ver_pre rc1
%global sof_ver_rel %{?sof_ver_pre:.%{sof_ver_pre}}
%global sof_ver_pkg0 %{sof_ver}%{?sof_ver_pre:-%{sof_ver_pre}}
%global sof_ver_pkg v%{sof_ver_pkg0}

%global with_sof_addon 0
%global sof_ver_addon 0

%global tplg_version 1.2.4

Summary:        Firmware and topology files for Sound Open Firmware project
Name:           alsa-sof-firmware
Version:        2025.12.2
Release:        2.hum1.pigeon
License:        BSD-3-Clause AND Apache-2.0
URL:            https://github.com/thesofproject/sof-bin
Source:         https://github.com/thesofproject/sof-bin/releases/download/%{sof_ver_pkg}/sof-bin-%{sof_ver_pkg0}.tar.gz
BuildRequires:  alsa-topology >= 1.2.4
BuildRequires:  alsa-topology-utils >= 1.2.4
Conflicts:      alsa-firmware <= 1.2.1-6

# noarch, since the package is firmware
BuildArch:      noarch

%description
This package contains the firmware binaries for the Sound Open Firmware project.

%package debug
Requires:       alsa-sof-firmware
Summary:        Debug files for Sound Open Firmware project
License:        BSD-3-Clause

%description debug
This package contains the debug files for the Sound Open Firmware project.

%prep
%autosetup -n sof-bin-2025.12.2

mkdir -p firmware/intel

%install
mkdir -p %{buildroot}%{_firmwarepath}/intel/sof
mkdir -p %{buildroot}%{_firmwarepath}/intel/sof-tplg
cp -a firmware/intel/sof/*.ri %{buildroot}%{_firmwarepath}/intel/sof/
cp -a firmware/intel/sof-tplg/*.tplg %{buildroot}%{_firmwarepath}/intel/sof-tplg/

%files
%license LICENSE
%{_firmwarepath}/intel/sof/
%{_firmwarepath}/intel/sof-tplg/

%files debug
%license LICENSE
%{_datadir}/alsa/sof/

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 2025.12.2-1.hum1.pigeon
- Initial Kestrel package (independent recipe)