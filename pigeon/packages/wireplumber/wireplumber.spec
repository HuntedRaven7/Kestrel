# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/pipewire/wireplumber (tag 0.5.8).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           wireplumber
Version:        0.5.8
Release:        1%{?dist}
Summary:        A modular session/policy manager for PipeWire

License:        MIT
URL:            https://github.com/pipewire/wireplumber
Source0:        https://github.com/pipewire/wireplumber/archive/refs/tags/%{version}.tar.gz

BuildRequires:  gettext
BuildRequires:  meson gcc pkgconfig
BuildRequires:  pkgconfig(glib-2.0) >= 2.70.0
BuildRequires:  pkgconfig(gobject-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(gmodule-2.0)
BuildRequires:  pkgconfig(libspa-0.2) >= 0.2
BuildRequires:  pkgconfig(libpipewire-0.3) >= 0.3.26
BuildRequires:  pkgconfig(lua) >= 5.1
BuildRequires:  lua-devel
BuildRequires:  pkgconfig(systemd)
BuildRequires:  systemd-devel >= 184
BuildRequires:  systemd-rpm-macros
BuildRequires:  gobject-introspection-devel
BuildRequires:  python3-lxml doxygen
%{?systemd_ordering}

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

Provides:       pipewire-session-manager
Conflicts:      pipewire-session-manager

%package        libs
Summary:        Libraries for WirePlumber clients
Recommends:     %{name}%{?_isa} = %{version}-%{release}

%description libs
This package contains the runtime libraries for any application that wishes
to interface with WirePlumber.

%description
WirePlumber is a modular session/policy manager for PipeWire and a
GObject-based high-level library that wraps PipeWire's API, providing
convenience for writing the daemon's modules as well as external tools for
managing PipeWire.

%prep
%autosetup -p1 -n wireplumber-%{version}

%build
%meson -Dsystem-lua=true \
       -Ddoc=disabled \
       -Dsystemd=enabled \
       -Dsystemd-user-service=true \
       -Dintrospection=enabled \
       -Delogind=disabled
%meson_build

%install
%meson_install

# Create local config skeleton
mkdir -p %{buildroot}%{_sysconfdir}/wireplumber/{bluetooth.lua.d,common,main.lua.d,policy.lua.d}

# Create missing empty system config dirs for other packages to drop files in
mkdir -p %{buildroot}%{_datadir}/wireplumber/wireplumber.conf.d

# Generate bash completion for wpctl (dir first: the redirect target's
# parent does not exist in a fresh buildroot and sh -e aborts on it)
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/wpctl --bash-completion > %{buildroot}%{_datadir}/bash-completion/completions/wpctl 2>/dev/null || :

%find_lang %{name}

%posttrans
%systemd_user_post %{name}.service

%preun
%systemd_user_preun %{name}.service

%files
%license LICENSE
%{_bindir}/wireplumber
%{_bindir}/wpctl
%{_bindir}/wpexec
%dir %{_sysconfdir}/wireplumber
%dir %{_sysconfdir}/wireplumber/bluetooth.lua.d
%dir %{_sysconfdir}/wireplumber/common
%dir %{_sysconfdir}/wireplumber/main.lua.d
%dir %{_sysconfdir}/wireplumber/policy.lua.d
%{_datadir}/wireplumber/
%{_datadir}/zsh/site-functions/_wpctl
%{_datadir}/bash-completion/completions/wpctl
%{_userunitdir}/wireplumber.service
%{_userunitdir}/wireplumber@.service

%files libs -f %{name}.lang
%license LICENSE
%dir %{_libdir}/wireplumber-0.5/
%{_libdir}/wireplumber-0.5/libwireplumber-*.so
%{_libdir}/libwireplumber-*.so.*
%{_libdir}/girepository-1.0/Wp-0.5.typelib

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 0.5.8-1.hum1.pigeon
- Align with Fedora/Utah: add libs subpackage, proper BuildRequires,
  disable docs/installation tests, use %find_lang
- Add pkgconfig(gmodule-2.0), python3-lxml, doxygen BuildRequires