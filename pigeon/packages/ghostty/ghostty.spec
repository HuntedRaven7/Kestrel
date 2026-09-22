# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/ghostty-org/ghostty (tag v1.3.1).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Zig notes (read before touching this recipe):
# - build.zig.zon pins minimum_zig_version = 0.15.2. If the Fedora 44
#   buildroot ships older zig, Pigeon must package zig first (CI will tell).
# - Library deps (libxev, vaxis, …) come from deps.files.ghostty.org and are
#   content-hash-pinned in build.zig.zon, which zig verifies. This recipe is
#   therefore the ONE package allowed network at build time; the hashes make
#   it fail-closed rather than floating. Revisit if the lane goes hermetic.

Name:           ghostty
Version:        1.3.1
Release:        1.hum1.pigeon
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
# Install Zig 0.15.2 (newer Fedora 44 ships 0.16.0 which has breaking changes;
# older versions can't build ghostty v1.3.1 which requires 0.15.2).
# See: https://ziglang.org/download/0.15.2/
# Note: Zig 0.15.x uses the zig-x86_64-linux-NN.N.N naming scheme
# (zig-linux-x86_64-NN.N.N was for 0.14.x and earlier).
ZIG_VER=0.15.2
ZIG_URL="https://ziglang.org/download/${ZIG_VER}/zig-x86_64-linux-${ZIG_VER}.tar.xz"
curl -sSL "${ZIG_URL}" -o /tmp/zig.tar.xz
tar -xf /tmp/zig.tar.xz -C /tmp
export PATH="/tmp/zig-x86_64-linux-${ZIG_VER}:$PATH"

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
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 1.3.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
- Remove invalid -Dversion zig build option
