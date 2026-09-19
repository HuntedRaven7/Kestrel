# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://gitlab.freedesktop.org/pipewire/pipewire (tag 1.6.8).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%global spaversion 0.2
%global __meson_auto_features disabled

Name:       pipewire-libs-extra
Summary:    PipeWire extra plugins
Version:    1.6.8
Release:    1.hum1.pigeon
License:    MIT
URL:        https://pipewire.org/

Source0:    https://gitlab.freedesktop.org/pipewire/pipewire/-/archive/1.6.8/pipewire-1.6.8.tar.gz

BuildRequires:  alsa-lib-devel
BuildRequires:  meson >= 0.49.0
BuildRequires:  gcc-c++
BuildRequires:  git
BuildRequires:  liblc3plus-devel
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(bluez) >= 4.101
BuildRequires:  pkgconfig(libfreeaptx)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libswscale)
BuildRequires:  pkgconfig(lilv-0)
BuildRequires:  sbc-devel

Requires:       pipewire >= %{version}

%description
PipeWire extra plugins: aptX, LC3plus and FFmpeg SPA plugins.

%prep
%autosetup -p1 -n pipewire-1.6.8

%build
%meson \
  -D examples=disabled \
  -D bluez5=enabled \
  -D bluez5-codec-aptx=enabled \
  -D bluez5-codec-ldac-dec=disabled \
  -D bluez5-codec-lc3plus=enabled \
  -D ffmpeg=enabled \
  -D lv2=enabled \
  -D session-managers=[]
%meson_build \
    spa-codec-bluez5-aptx \
    spa-codec-bluez5-lc3plus \
    spa-ffmpeg

%install
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/bluez5/libspa-codec-bluez5-aptx.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-aptx.so
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/bluez5/libspa-codec-bluez5-lc3plus.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-lc3plus.so
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/ffmpeg/libspa-ffmpeg.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/ffmpeg/libspa-ffmpeg.so

%files
%license COPYING
%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-aptx.so
%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-lc3plus.so
%dir %{_libdir}/spa-%{spaversion}/ffmpeg
%{_libdir}/spa-%{spaversion}/ffmpeg/libspa-ffmpeg.so

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.6.8-1.hum1.pigeon
- Initial Kestrel package (independent recipe)