# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/lassekongo83/adw-gtk3 (tag v6.4).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           adw-gtk3-theme
Version:        6.4
Release:        1.hum1.pigeon
Summary:        The theme from libadwaita ported to GTK-3
BuildArch:      noarch

License:        LGPL-2.1-only
URL:            https://github.com/lassekongo83/adw-gtk3
Source0:        https://github.com/lassekongo83/adw-gtk3/releases/download/v%{version}/adw-gtk3v%{version}.tar.xz
Source1:        https://raw.githubusercontent.com/lassekongo83/adw-gtk3/refs/heads/main/README.md#/README.md.upstream
Source2:        https://raw.githubusercontent.com/lassekongo83/adw-gtk3/refs/heads/main/LICENSE#/LICENSE.upstream

%description
The theme from libadwaita ported to GTK-3.

%prep
%autosetup -c

%install
install -Dpm644 %{SOURCE1} README.md
install -Dpm644 %{SOURCE2} LICENSE
mkdir -p %{buildroot}%{_datadir}/themes
cp -ap adw-gtk3 %{buildroot}%{_datadir}/themes/adw-gtk3/
cp -ap adw-gtk3-dark %{buildroot}%{_datadir}/themes/adw-gtk3-dark/

%files
%license LICENSE
%doc README.md
%{_datadir}/themes/adw-gtk3/
%{_datadir}/themes/adw-gtk3-dark/

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 6.4-1.hum1.pigeon
- Initial Kestrel package (independent recipe)