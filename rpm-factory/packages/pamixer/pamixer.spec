Name:           pamixer
Version:        1.6
Release:        %autorelease
Summary:        PulseAudio command line mixer

License:        GPL-3.0-or-later
URL:            https://github.com/cdemoulins/pamixer
Source:         %{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  meson
BuildRequires:  pkgconfig(cxxopts)
BuildRequires:  pkgconfig(libpulse)
# require *-static for header-only library
BuildRequires:  cxxopts-static

%description
Pamixer is like amixer but for PulseAudio. It can control the volume
levels of the sinks.


%prep
%autosetup


%build
%meson
%meson_build


%install
%meson_install


%files
%doc README.rst
%license COPYING
%{_bindir}/%{name}
%{_mandir}/man1/%{name}.1*


%changelog
%autochangelog
