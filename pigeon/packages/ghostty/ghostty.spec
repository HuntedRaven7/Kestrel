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
BuildRequires:  zig >= 0.15.2
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  pkgconfig(fontconfig)

%description
Ghostty terminal emulator — default terminal of the Warbler desktop.

%prep
%autosetup -n ghostty-%{version} -p1

%build
zig build -Doptimize=ReleaseFast -Dversion=v%{version} -p %{buildroot}%{_prefix}

%install
# zig build -p installs above; nothing more to stage.

%files
%license LICENSE
%{_bindir}/ghostty
%{_datadir}/applications/com.mitchellh.ghostty.desktop
%{_datadir}/ghostty/
%{_datadir}/icons/hicolor/*/apps/com.mitchellh.ghostty*.png
%{_datadir}/terminfo/
%{_mandir}/man1/ghostty.1*
%{_mandir}/man5/ghostty.5*

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 1.3.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
