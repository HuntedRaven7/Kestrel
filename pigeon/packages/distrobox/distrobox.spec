# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/89luca89/distrobox (tag 1.8.2.5).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%global debug_package %{nil}

%global forgeurl https://github.com/89luca89/distrobox
%global tag 1.8.2.5
%forgemeta

Name: distrobox
Version: 1.8.2.5
Release: 1.hum1.pigeon
Summary: Another tool for containerized command line environments on Linux
License: GPL-3.0-only
URL:     https://github.com/89luca89/distrobox
Source0: https://github.com/89luca89/distrobox/archive/refs/tags/1.8.2.5/distrobox-1.8.2.5.tar.gz

BuildArch: noarch

Requires: (podman or %{_bindir}/docker)
Requires: %{_bindir}/basename
Requires: %{_bindir}/find
Requires: %{_bindir}/grep
Requires: %{_bindir}/sed
Requires: hicolor-icon-theme

Suggests: bash-completions

%description
Use any linux distribution inside your terminal. Distrobox uses podman
or docker to create containers using the linux distribution of your
choice. Created container will be tightly integrated with the host,
allowing to share the HOME directory of the user, external storage,
external usb devices and graphical apps (X11/Wayland) and audio.

%prep
%autosetup

%build

%install
./install -P %{buildroot}/%{_prefix}

%check
%{buildroot}%{_bindir}/%{name} list -V
for i in create enter export init list rm stop host-exec; do
    %{buildroot}%{_bindir}/%{name}-$i -V
done

%files
%license LICENSE
%{_bindir}/distrobox
%{_bindir}/distrobox-*

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 1.8.2.5-1.hum1.pigeon
- Initial Kestrel package (independent recipe)