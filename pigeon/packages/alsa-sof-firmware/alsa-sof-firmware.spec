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
Release:        3.hum1.pigeon
License:        BSD-3-Clause AND Apache-2.0
URL:            https://github.com/thesofproject/sof-bin
Source:         https://github.com/thesofproject/sof-bin/releases/download/%{sof_ver_pkg}/sof-bin-%{sof_ver_pkg0}.tar.gz
BuildRequires:  alsa-topology >= 1.2.4
BuildRequires:  alsa-topology-utils >= 1.2.4
BuildRequires:  xz
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
%autosetup -n sof-bin-%{sof_ver_pkg0}

mkdir -p firmware/intel

for d in sof sof-ipc4 sof-ipc4-lib sof-ipc4-tplg sof-tplg; do \
  mv "${d}" firmware/intel; \
done

ln -s sof-ipc4-tplg firmware/intel/sof-ace-tplg

%if 0%{?with_sof_addon}
tar xvzf %{SOURCE3}
mv sof-tplg-v%{sof_ver_addon}/*.tplg firmware/intel/sof-tplg
%endif

# remove NXP firmware files
rm Notice.NXP LICENCE.NXP
rm -rf firmware/intel/sof-tplg/sof-imx8*

# remove Mediatek firmware files
rm -rf firmware/intel/sof-tplg/sof-mt8*

# use xz compression
xz -z %{_xz_opts} manifest.txt
for d in sof sof-ipc4; do \
  find -P "firmware/intel/${d}" -type f -name "*.ri" -exec xz -z %{_xz_opts} {} \;
  for f in $(find -P "firmware/intel/${d}" -type l -name "*.ri"); do \
    l=$(readlink "${f}"); \
    n=$(dirname "${f}"); \
    b=$(basename "${f}"); \
    rm "${f}"; \
    pushd "${n}"; \
    ln -svf "${l}.xz" "${b}.xz"; \
    popd; \
  done; \
done
for d in sof-ipc4-lib; do \
  for e in bin llext; do \
    find -P "firmware/intel/${d}"  -type f -name "*.${e}" -exec xz -z %{_xz_opts} {} \;
    for f in $(find -P "firmware/intel/${d}" -type l -name "*.${e}"); do \
      l=$(readlink "${f}"); \
      n=$(dirname "${f}"); \
      b=$(basename "${f}"); \
      rm "${f}"; \
      pushd "${n}"; \
      ln -svf "${l}.xz" "${b}.xz"; \
      popd; \
    done; \
  done; \
done
for d in sof-tplg sof-ipc4-tplg; do \
  find -P "firmware/intel/${d}"  -type f -name "*.tplg" -exec xz -z %{_xz_opts} {} \;
done

%build
# SST topology files (not SOF related, but it's a Intel hw support
# and this package seems a good place to distribute them
alsatplg -c /usr/share/alsa/topology/hda-dsp/skl_hda_dsp_generic-tplg.conf \
         -o firmware/skl_hda_dsp_generic-tplg.bin
# use xz compression
xz -z %{_xz_opts} firmware/*.bin
chmod 0644 firmware/*.bin.xz

%install
mkdir -p %{buildroot}%{_firmwarepath}
cp -ra firmware/* %{buildroot}%{_firmwarepath}

# gather files and directories
FILEDIR=$(pwd)
pushd %{buildroot}/%{_firmwarepath}
find -P . -name "*.ri.xz" | sed -e '/^.$/d' >> $FILEDIR/alsa-sof-firmware.files
find -P . -name "*.tplg" | sed -e '/^.$/d' >> $FILEDIR/alsa-sof-firmware.files
find -P . -name "*.tplg.xz" | sed -e '/^.$/d' >> $FILEDIR/alsa-sof-firmware.files
find -P . -name "*.llext.xz" | sed -e '/^.$/d' >> $FILEDIR/alsa-sof-firmware.files
find -P intel/sof-ipc4-lib -name "*.bin.xz" | sed -e '/^.$/d' >> $FILEDIR/alsa-sof-firmware.files
find -P . -name "*.ldc" | sed -e '/^.$/d' > $FILEDIR/alsa-sof-firmware.debug-files
find -P . -type d | sed -e '/^.$/d' > $FILEDIR/alsa-sof-firmware.dirs
popd
sed -i -e 's:^./::' alsa-sof-firmware.{files,debug-files,dirs}
sed -i -e 's!^!/usr/lib/firmware/!' alsa-sof-firmware.{files,debug-files,dirs}
sed -e 's/^/%%dir /' alsa-sof-firmware.dirs >> alsa-sof-firmware.files
cat alsa-sof-firmware.files

%files -f alsa-sof-firmware.files
%license LICENCE*
%doc README*
%doc manifest.txt.xz
%dir %{_firmwarepath}

# Licence: 3-clause BSD
%{_firmwarepath}/*.bin.xz

# Licence: 3-clause BSD
# .. for files with suffix .tplg
%{_firmwarepath}/intel/sof-tplg/*.tplg.xz
%{_firmwarepath}/intel/sof-ipc4-tplg/*.tplg.xz
%{_firmwarepath}/intel/sof-ace-tplg

# Licence: SOF (3-clause BSD plus others)
# .. for files with suffix .ri

%files debug -f alsa-sof-firmware.debug-files

%pretrans -p <lua>
path = "%{_firmwarepath}/intel/sof-tplg"
st = posix.stat(path)
if st and st.type == "link" then
  os.remove(path)
end

path1 = "%{_firmwarepath}/intel/sof-ace-tplg"
path2 = "%{_firmwarepath}/intel/sof-ipc4-tplg"
st = posix.stat(path1)
if st and st.type == "directory" then
  os.rename(path1, path2)
end

%changelog
* Sat Sep 19 2026 Kestrel <kestrel@localhost> - 2025.12.2-3.hum1.pigeon
- Rework %%prep/%%install/%%files on Fedora's layout: rearrange tarball
  into firmware/intel, xz-compress, generate file lists (old paths did
  not exist in current sof-bin releases)
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 2025.12.2-2.hum1.pigeon
- Initial Kestrel package (independent recipe)