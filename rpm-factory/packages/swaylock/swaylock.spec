Name:       swaylock
Version:    1.8.6
Release:    %{autorelease}
Summary:    Screen locker for Wayland

License:    MIT
URL:        https://github.com/swaywm/swaylock
Source0:    %{url}/releases/download/v%{version}/%{name}-%{version}.tar.gz
Source1:    %{url}/releases/download/v%{version}/%{name}-%{version}.tar.gz.sig
# gpg2 --export --armor --export-options export-minimal 34FF9526CFEF0E97A340E2E40FDE7BE0E88F5E48 >gpgkey-E88F5E48.asc
Source2:    gpgkey-E88F5E48.asc

BuildRequires:  gcc
BuildRequires:  gnupg2
BuildRequires:  meson >= 0.59.0
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(gdk-pixbuf-2.0)
BuildRequires:  pkgconfig(wayland-client) >= 1.20.0
BuildRequires:  pkgconfig(wayland-protocols) >= 1.25
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  scdoc

%description
swaylock is a screen locking utility for Wayland compositors.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup

%build
%meson
%meson_build

%install
%meson_install

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_mandir}/man1/%{name}.1*
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%{bash_completions_dir}/%{name}
%{fish_completions_dir}/%{name}.fish
%{zsh_completions_dir}/_%{name}


%changelog
%{autochangelog}
