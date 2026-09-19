# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: http://www.kernel.org/ (version 20260810).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%global debug_package %{nil}

%global _firmwarepath	/usr/lib/firmware
%define _binaries_in_noarch_packages_terminate_build 0

Name:		linux-firmware
Version:	20260810
Release:	2.hum1.pigeon
Summary:	Firmware files used by the Linux kernel
License:	GPL-1.0-or-later AND GPL-2.0-or-later AND MIT AND LicenseRef-Callaway-Redistributable-no-modification-permitted
URL:		http://www.kernel.org/
BuildArch:	noarch

Source0:	https://www.kernel.org/pub/linux/kernel/firmware/linux-firmware-20260810.tar.xz

BuildRequires:	make
BuildRequires:	git-core
BuildRequires:	python3

Requires:	linux-firmware-whence = %{version}-%{release}

%description
This package includes firmware files required for some devices to
operate.

%package whence
Summary:	WHENCE License file
License:	GPL-1.0-or-later AND GPL-2.0-or-later AND MIT AND LicenseRef-Callaway-Redistributable-no-modification-permitted
%description whence
This package contains the WHENCE license file which documents the vendor license details.

# GPU firmwares
%package -n amd-gpu-firmware
Summary:	Firmware for AMD GPUs
License:	LicenseRef-Callaway-Redistributable-no-modification-permitted
Requires:	linux-firmware-whence = %{version}-%{release}
%description -n amd-gpu-firmware
Firmware for AMD amdgpu and radeon GPUs.

%package -n intel-gpu-firmware
Summary:	Firmware for Intel GPUs
License:	LicenseRef-Callaway-Redistributable-no-modification-permitted
Requires:	linux-firmware-whence = %{version}-%{release}
%description -n intel-gpu-firmware
Firmware for Intel GPUs including GuC (Graphics Microcontroller), HuC (HEVC/H.265
Microcontroller) and DMC (Display Microcontroller) firmware for Skylake and later
platforms.

%package -n nvidia-gpu-firmware
Summary:	Firmware for NVIDIA GPUs
License:	LicenseRef-Callaway-Redistributable-no-modification-permitted
Requires:	linux-firmware-whence = %{version}-%{release}
%description -n nvidia-gpu-firmware
Firmware for NVIDIA GPUs.

%prep
%autosetup -n linux-firmware-20260810 -p1

%build
# Firmware packages don't build anything, just copy files
:

%install
mkdir -p %{buildroot}%{_firmwarepath}
cp -a * %{buildroot}%{_firmwarepath}/

# Remove files that shouldn't be installed
rm -f %{buildroot}%{_firmwarepath}/*.txt
rm -f %{buildroot}%{_firmwarepath}/*.md
rm -f %{buildroot}%{_firmwarepath}/README
rm -rf %{buildroot}%{_firmwarepath}/LICENSE*
rm -rf %{buildroot}%{_firmwarepath}/COPYING*
rm -f %{buildroot}%{_firmwarepath}/WHENCE
rm -f %{buildroot}%{_firmwarepath}/*.txt
rm -f %{buildroot}%{_firmwarepath}/Makefile
rm -f %{buildroot}%{_firmwarepath}/*.patch

%files
%license LICENSE*
%{_firmwarepath}/*
%exclude %{_firmwarepath}/WHENCE

%files whence
%license GPL-1.0-or-later AND GPL-2.0-or-later AND MIT AND LicenseRef-Callaway-Redistributable-no-modification-permitted
%{_firmwarepath}/WHENCE

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 20260810-2.hum1.pigeon
- Initial Kestrel package (independent recipe)