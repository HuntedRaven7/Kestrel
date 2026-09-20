# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://gitlab.freedesktop.org/pipewire/pipewire (tag 1.6.8).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%global majorversion 1
%global minorversion 6
%global microversion 8

%global apiversion   0.3
%global spaversion   0.2
%global soversion    0
%global libversion   %{soversion}.%(bash -c '((intversion = (%{minorversion} * 100) + %{microversion})); echo ${intversion}').0
%global ms_version   0.4.2

%global baserelease 3

%bcond_without alsa
%bcond_without vulkan
%bcond_without bluez
%bcond_with fdk_aac
%bcond_with freeaptx
%bcond_with lc3plus

%if 0%{?rhel} && 0%{?rhel} < 9
%bcond_with pulse
%bcond_with jack
%else
%bcond_without pulse
%bcond_without jack
%endif

%bcond_with onnx
%bcond_without v4l2

Name:           pipewire
Summary:        Media Sharing Server
Version:        1.6.8
Release:        3.hum1.pigeon
License:        MIT
URL:            https://pipewire.org/
Source0:        https://gitlab.freedesktop.org/pipewire/pipewire/-/archive/1.6.8/pipewire-1.6.8.tar.gz
Source1:        pipewire.sysusers

BuildRequires:  alsa-lib-devel
BuildRequires:  avahi-devel
%if 0%{?with_bluez}
BuildRequires:  bluez-libs-devel
%endif
BuildRequires:  docbook-dtds
BuildRequires:  docbook-style-xsl
BuildRequires:  doxygen
%if 0%{?with_fdk_aac}
BuildRequires:  fdk-aac-devel
%endif
BuildRequires:  gcc-c++
BuildRequires:  gstreamer1-devel
%if 0%{?with_freeaptx}
BuildRequires:  libfreeaptx-devel
%endif
%if 0%{?with_lc3plus}
BuildRequires:  liblc3plus-devel
%endif
BuildRequires:  libsndfile-devel
BuildRequires:  libva-devel
BuildRequires:  lilv-devel
BuildRequires:  lua-devel
BuildRequires:  meson >= 0.49.0
BuildRequires:  ncurses-devel
%if 0%{?with_bluez}
BuildRequires:  pkgconfig(bluez) >= 4.101
%endif
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(glib-2.0) >= 2.46.0
BuildRequires:  pkgconfig(gobject-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(gstreamer-1.0)
BuildRequires:  pkgconfig(gio-unix-2.0) >= 2.46.0
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(opus)
BuildRequires:  pkgconfig(sndfile)
BuildRequires:  pkgconfig(vulkan)
BuildRequires:  python3-pyparsing
BuildRequires:  ragel
BuildRequires:  sbc-devel
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
BuildRequires:  vala
%if (0%{?fedora} && 0%{?fedora} <= 44) || (0%{?rhel} && 0%{?rhel} < 11)
BuildRequires:  webrtc-audio-processing-devel
%else
BuildRequires:  webrtc-audio-processing2-devel
%endif

Requires:       rtkit
Requires:       wireplumber

%description
PipeWire is a server and user space API to handle multimedia pipelines.
It supports low latency capture, graph-based processing, and inter-application
sharing of multimedia content.

%package libs
Summary:        PipeWire runtime libraries
License:        MIT
%description libs
PipeWire runtime libraries.

%package gstreamer
Summary:        PipeWire GStreamer elements
Requires:       pipewire-libs%{?_isa} = %{version}-%{release}
Requires:       gstreamer1%{?_isa}

%description gstreamer
PipeWire GStreamer elements.

%package jack-audio-connection-kit
Summary:        PipeWire JACK replacement
Requires:       pipewire%{?_isa} = %{version}-%{release}
Requires:       jack-audio-connection-kit-libs%{?_isa} = %{version}-%{release}
Provides:       jack-audio-connection-kit = %{version}-%{release}
Obsoletes:      jack-audio-connection-kit < %{version}

%description jack-audio-connection-kit
PipeWire JACK replacement.

%package jack-audio-connection-kit-libs
Summary:        PipeWire JACK replacement libraries
License:        MIT
%description jack-audio-connection-kit-libs
PipeWire JACK replacement libraries.

%package pulseaudio
Summary:        PipeWire PulseAudio replacement
Requires:       pipewire%{?_isa} = %{version}-%{release}
Requires:       pipewire-libs%{?_isa} = %{version}-%{release}
Provides:       pulseaudio = %{version}-%{release}
Obsoletes:      pulseaudio < %{version}

%description pulseaudio
PipeWire PulseAudio replacement.

%package pulseaudio-libs
Summary:        PipeWire PulseAudio replacement libraries
License:        MIT

%description pulseaudio-libs
PipeWire PulseAudio replacement libraries.

%package pulseaudio-utils
Summary:        PipeWire PulseAudio utilities
Requires:       pipewire-pulseaudio%{?_isa} = %{version}-%{release}
Requires:       pipewire%{?_isa} = %{version}-%{release}
Provides:       pulseaudio-utils = %{version}-%{release}
Obsoletes:      pulseaudio-utils < %{version}

%description pulseaudio-utils
PipeWire PulseAudio utilities.

%package devel
Summary:        Development files for PipeWire
Requires:       pipewire-libs%{?_isa} = %{version}-%{release}
Requires:       pkgconfig
Requires:       pkgconfig(pipewire-%{apiversion})
Requires:       pkgconfig(pipewire-%{spaversion})
Requires:       pkgconfig(spa)
%description devel
Development files for PipeWire.

%package utils
Summary:        PipeWire utilities
Requires:       pipewire%{?_isa} = %{version}-%{release}

%description utils
PipeWire utilities.

%prep
%autosetup -n pipewire-1.6.8 -p1

%build
%meson \
  -Dsystemd=true \
  -Dpipewire-alsa=%{?with_alsa:enabled} \
  -Dpipewire-jack=%{?with_jack:enabled} \
  -Dpipewire-pulse=%{?with_pulse:enabled} \
  -Dpipewire-vulkan=%{?with_vulkan:enabled} \
  -Dvalgrind=disabled \
  -Dbluez5=%{?with_bluez:enabled} \
  -Dbluez5-codec-ldac=disabled \
  -Dbluez5-codec-lc3plus=disabled \
  -Dbluez5-codec-aptx=disabled \
  -Dbluez5-codec-aptxhd=disabled \
  -Dbluez5-codec-ldac-dec=disabled \
  -Dbluez5-codec-lc3=enabled \
  -Dffmpeg=enabled \
  -Dlibcamera=disabled \
  -Donnx=disabled \
  -Droc=disabled \
  -Dv4l2=disabled \
  -Drocm=disabled \
  -Dsession-managers=[] \
  -Dlibcamera-plugin=disabled \
  -Dv4l2-plugin=disabled \
  -Droc-plugin=disabled \
  -Dffado-plugin=disabled \
  -Dlibmysofa-plugin=disabled \
  -Dlv2-plugin=disabled \
  -Droc-plugin=disabled \
  -Dpipewire-jackserver-plugin=disabled \
  -Dlibcamera-plugin=disabled \
  -Dv4l2-plugin=disabled \
  -Droc-plugin=disabled \
  -Dffado-plugin=disabled \
  -Dlibmysofa-plugin=disabled \
  -Dlv2-plugin=disabled \
  -Droc-plugin=disabled \
  -Dpipewire-jackserver-plugin=disabled
%meson_build

%install
%meson_install

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%files
%license COPYING
%{_bindir}/pw-*
%{_libdir}/libpipewire-*.so.*
%{_libdir}/pipewire-%{apiversion}/
%{_libdir}/spa-%{spaversion}/
%{_datadir}/pipewire/
%{_datadir}/pipewire/jack.conf
%{_sysconfdir}/pipewire/
%{_sysconfdir}/alsa/conf.d/99-pipewire-default.conf
%{_sysconfdir}/alsa/conf.d/99-pipewire-0.conf
%{_unitdir}/pipewire.service
%{_unitdir}/pipewire-pulse.service
%{_unitdir}/pipewire-pulse.socket
%{_unitdir}/pipewire.socket
%{_sysconfdir}/xdg/autostart/pipewire.desktop

%files libs
%license COPYING
%{_libdir}/libpipewire-*.so.*
%{_libdir}/pipewire-%{apiversion}/
%{_libdir}/spa-%{spaversion}/
%{_datadir}/pipewire/
%{_datadir}/pipewire/jack.conf
%{_sysconfdir}/pipewire/
%{_sysconfdir}/alsa/conf.d/99-pipewire-default.conf
%{_sysconfdir}/alsa/conf.d/99-pipewire-0.conf

%files gstreamer
%{_libdir}/gstreamer-1.0/libgstpipewire.so

%files jack-audio-connection-kit
%{_bindir}/pw-jack
%{_libdir}/pipewire-%{apiversion}/jack/
%{_libdir}/spa-%{spaversion}/jack/

%files jack-audio-connection-kit-libs
%license COPYING
%{_libdir}/libjack.so.*
%{_libdir}/spa-%{spaversion}/jack/

%files pulseaudio
%{_bindir}/pw-pulse
%{_libdir}/pipewire-%{apiversion}/pulse/
%{_libdir}/spa-%{spaversion}/pulse/

%files pulseaudio-libs
%license COPYING
%{_libdir}/libpulse.so.*
%{_libdir}/spa-%{spaversion}/pulse/

%files pulseaudio-utils
%{_bindir}/pw-pulse
%{_libdir}/pipewire-%{apiversion}/pulse/
%{_libdir}/spa-%{spaversion}/pulse/

%files devel
%{_libdir}/libpipewire-*.so
%{_libdir}/pkgconfig/pipewire-*.pc
%{_includedir}/pipewire/
%{_includedir}/spa/

%files utils
%{_bindir}/pw-*
%{_mandir}/man1/pw-*.1*

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.6.8-3.hum1.pigeon
- Initial Kestrel package (independent recipe)
- Disable optional codecs (fdk-aac, freeaptx, lc3plus) by default for Fedora 44 compat
- Fix webrtc-audio-processing version for Fedora 44+