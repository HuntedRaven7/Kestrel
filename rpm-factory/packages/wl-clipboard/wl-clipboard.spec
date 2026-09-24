Name:           wl-clipboard
Version:        2.3.0
Release:        %autorelease
Summary:        Command-line copy/paste utilities for Wayland

License:        GPL-3.0-or-later
URL:            https://github.com/bugaevc/wl-clipboard
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  meson
BuildRequires:  gcc
BuildRequires:  wayland-devel
BuildRequires:  wayland-protocols-devel >= 1.39

Recommends:     xdg-utils
Recommends:     mailcap

%description
Command-line Wayland clipboard utilities, `wl-copy` and `wl-paste`,
that let you easily copy data between the clipboard and Unix pipes,
sockets, files and so on.

%prep
%autosetup -C

%build
%meson
%meson_build

%install
%meson_install

%check
%meson_test

%files
%license COPYING
%doc README.md
%{_bindir}/wl-copy
%{_bindir}/wl-paste
%{_mandir}/man1/wl-clipboard.1.*
%{_mandir}/man1/wl-copy.1.*
%{_mandir}/man1/wl-paste.1.*
%{_datadir}/bash-completion/completions/wl-*
%{_datadir}/fish/vendor_completions.d/wl-*
%{_datadir}/zsh/site-functions/_wl-*

%changelog
%autochangelog
