# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/ghostty-org/ghostty (tag v1.3.1).
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Zig 0.15.2 is supplied as a digest-locked extra source. The archive is
# unpacked in %install, so rpmbuild never needs network access.

Name:           ghostty
Version:        1.3.1
Release:        1.hum1.rpmfactory
Summary:        Fast, feature-rich terminal emulator
License:        MIT
URL:            https://github.com/ghostty-org/ghostty
Source0:        https://github.com/ghostty-org/ghostty/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(gtk4-layer-shell-0)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  blueprint-compiler
BuildRequires:  xz

# libghostty-vt.so* is built by Zig without a GNU build-id note; find-debuginfo
# --strict-build-id would abort the build on it. Undefine only this one check so
# the lib is packaged (find-debuginfo still skips it); all other checks stay.
%undefine _missing_build_ids_terminate_build

%description
Ghostty terminal emulator — default terminal of the Warbler desktop.

%prep
%autosetup -n ghostty-%{version} -p1

%build
# Compile and stage happens in %install: rpmbuild re-creates %{buildroot}
# between %build and %install, so zig installs done here would be wiped.

%install
# Install the locked Zig 0.15.2 archive supplied by source_pipeline.py.
ZIG_VER=0.15.2
ZIG_ARCHIVE="%{_sourcedir}/zig-x86_64-linux-${ZIG_VER}.tar.xz"
test -f "${ZIG_ARCHIVE}"
tar -xf "${ZIG_ARCHIVE}" -C /tmp
export PATH="/tmp/zig-x86_64-linux-${ZIG_VER}:$PATH"

# Seed Zig's package cache from the digest-locked dependency archives. The
# Tine sandbox intentionally has no network access during rpmbuild.
ZIG_CACHE=/tmp/ghostty-zig-cache
mkdir -p "${ZIG_CACHE}"
for archive in "%{_sourcedir}"/*.tar.gz "%{_sourcedir}"/*.tar.zst "%{_sourcedir}"/*.tgz; do
  [ -f "${archive}" ] || continue
  case "$(basename "${archive}")" in
    v%{version}.tar.gz) continue ;;
  esac
  zig fetch --global-cache-dir "${ZIG_CACHE}" "${archive}" >/dev/null
done
export ZIG_GLOBAL_CACHE_DIR="${ZIG_CACHE}"

zig build -Doptimize=ReleaseFast -p %{buildroot}%{_prefix}

%files
%license LICENSE
%{_bindir}/ghostty
%{_prefix}/lib/libghostty-vt.so*
%{_includedir}/ghostty
%{_datadir}/applications/com.mitchellh.ghostty.desktop
%{_datadir}/ghostty/
%{_datadir}/icons/hicolor/*/apps/com.mitchellh.ghostty*.png
%{_datadir}/pkgconfig/libghostty-vt.pc
%{_datadir}/terminfo/
%{_mandir}/man1/ghostty.1*
%{_mandir}/man5/ghostty.5*

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 1.3.1-1.hum1.rpmfactory
- Initial Kestrel package (independent recipe)
- Remove invalid -Dversion zig build option
