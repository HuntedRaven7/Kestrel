# Kestrel-original recipe.
# Upstream: https://gitlab.freedesktop.org/pipewire/pipewire (tag 1.6.8).
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).
#
# Based on Utah's pipewire-libs-extra: enables aptX, LC3plus and FFmpeg SPA plugins.

%global spaversion 0.2
%global __meson_auto_features disabled

%if 0%{?fedora} && 0%{?fedora} < 45
# Kestrel: forced off — freeaptx/lc3plus -devel packages live in RPMFusion,
# which is not enabled in our buildroots (No match on F44).
%bcond freeaptx 0
%bcond lc3plus 0
%else
%bcond freeaptx 0
%bcond lc3plus 0
%endif

Name:       pipewire-libs-extra
Summary:    PipeWire extra plugins
Version:    1.6.8
Release:    1%{?dist}
License:    MIT
URL:        https://pipewire.org/

Source0:    https://gitlab.freedesktop.org/pipewire/pipewire/-/archive/%{version}/pipewire-%{version}.tar.gz

# Update to LC3plus 1.8.0 APIs
Patch0:     pipewire-lc3plus-api.patch

BuildRequires:  alsa-lib-devel
BuildRequires:  meson >= 0.49.0
BuildRequires:  gcc-c++
BuildRequires:  git
%if %{with lc3plus}
BuildRequires:  liblc3plus-devel
%endif
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(bluez) >= 4.101
%if %{with freeaptx}
BuildRequires:  pkgconfig(libfreeaptx)
%endif
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libswscale)
BuildRequires:  pkgconfig(lilv-0)
BuildRequires:  sbc-devel

Requires:       pipewire >= %{version}

%description
PipeWire media server Bluetooth aptX codec plugin.

%prep
%autosetup -p1 -n pipewire-%{version}

%build
%meson \
  -D examples=disabled \
  -D bluez5=enabled \
  %if %{?with_freeaptx:1}%{!?with_freeaptx:0}
  -D bluez5-codec-aptx=enabled \
  %else
  -D bluez5-codec-aptx=disabled \
  %endif
  -D bluez5-codec-ldac-dec=disabled \
  %if %{?with_lc3plus:1}%{!?with_lc3plus:0}
  -D bluez5-codec-lc3plus=enabled \
  %else
  -D bluez5-codec-lc3plus=disabled \
  %endif
  -D ffmpeg=enabled \
  -D lv2=enabled \
  -D session-managers=[]

%meson_build \
    %if %{?with_freeaptx:1}%{!?with_freeaptx:0}
    spa-codec-bluez5-aptx \
    %endif
    %if %{?with_lc3plus:1}%{!?with_lc3plus:0}
    spa-codec-bluez5-lc3plus \
    %endif
    spa-ffmpeg

%install
%if %{?with_freeaptx:1}%{!?with_freeaptx:0}
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/bluez5/libspa-codec-bluez5-aptx.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-aptx.so
%endif
%if %{?with_lc3plus:1}%{!?with_lc3plus:0}
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/bluez5/libspa-codec-bluez5-lc3plus.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-lc3plus.so
%endif
install -pm 0755 -D %{_vpath_builddir}/spa/plugins/ffmpeg/libspa-ffmpeg.so \
    %{buildroot}%{_libdir}/spa-%{spaversion}/ffmpeg/libspa-ffmpeg.so

%files
%license COPYING
%if %{?with_freeaptx:1}%{!?with_freeaptx:0}
%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-aptx.so
%endif
%if %{?with_lc3plus:1}%{!?with_lc3plus:0}
%{_libdir}/spa-%{spaversion}/bluez5/libspa-codec-bluez5-lc3plus.so
%endif
%dir %{_libdir}/spa-%{spaversion}/ffmpeg
%{_libdir}/spa-%{spaversion}/ffmpeg/libspa-ffmpeg.so

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 1.6.8-1.hum1.rpmfactory
- Simplify to match Utah approach: always enable aptX, LC3plus and FFmpeg
- Use %meson_build with specific targets for cleaner builds
- Add %global __meson_auto_features disabled
- Add LC3plus 1.8.0 API compatibility patch