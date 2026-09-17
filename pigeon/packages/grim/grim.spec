Name:		grim
Version:	1.5.0
Release:	%autorelease
Summary:	Screenshot tool for Sway

License:	MIT
URL:		https://gitlab.freedesktop.org/emersion/grim
Source0:	%{url}/-/releases/v%{version}/downloads/%{name}-%{version}.tar.gz
Source1:	%{url}/-/releases/v%{version}/downloads/%{name}-%{version}.tar.gz.sig
Source2:	dj3498u4hyyarh35rkjfnghbjxug6b19

BuildRequires:	pkgconfig(bash-completion)
BuildRequires:	pkgconfig(libjpeg)
BuildRequires:	pkgconfig(libpng)
BuildRequires:	pkgconfig(pixman-1)
BuildRequires:	pkgconfig(wayland-client)
BuildRequires:	pkgconfig(wayland-protocols) >= 1.37
BuildRequires:	pkgconfig(wayland-scanner)
BuildRequires:	scdoc
BuildRequires:	meson >= 0.59.0
BuildRequires:	gcc
BuildRequires:	gnupg2

%description
Grim is a command-line tool to grab images from Sway.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup

%build
%meson \
	-Dbash-completions=true \
	-Dfish-completions=true
%meson_build

%install
%meson_install

%files
%doc README.md
%license LICENSE
%{_bindir}/grim
%{_mandir}/man1/grim.1*
%{bash_completions_dir}/grim*
%{fish_completions_dir}/grim*

%changelog
%autochangelog
