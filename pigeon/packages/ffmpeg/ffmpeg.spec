# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://ffmpeg.org/ (tag 7.1).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

# For a complete build enable this
%bcond all_codecs 0

# Break dependency cycles by disabling certain optional dependencies.
%bcond bootstrap 0

%bcond vapoursynth 0
%bcond libbluray 0

%global pkg_suffix -free

%ifarch x86_64
%bcond vpl 1
%bcond vmaf 1
%else
%bcond vpl 0
%bcond vmaf 0
%endif

%ifarch s390 s390x riscv64
%bcond dc1394 0
%bcond ffnvcodec 0
%else
%bcond dc1394 1
%bcond ffnvcodec 1
%endif

%if 0%{?rhel}
%bcond chromaprint 0
%bcond flite 0
%else
%bcond chromaprint 0
%bcond flite 0
%endif

%ifarch x86_64
%bcond lto 1
%else
%bcond lto 0
%endif

%ifarch s390 s390x
%bcond ffnvcodec 0
%else
%bcond ffnvcodec 1
%endif

%if 0%{?rhel}
%bcond chromaprint 0
%bcond flite 0
%endif

%ifarch x86_64
%bcond vpl 1
%bcond vmaf 1
%else
%bcond vpl 0
%bcond vmaf 0
%endif

%ifarch s390 s390x
%bcond dc1394 0
%bcond ffnvcodec 0
%else
%bcond dc1394 1
%bcond ffnvcodec 1
%endif

%if 0%{?rhel}
%bcond chromaprint 0
%bcond flite 0
%else
%bcond chromaprint 0
%bcond flite 0
%endif

%ifarch x86_64
%bcond lto 1
%else
%bcond lto 0
%endif

Name:           ffmpeg
Version:        7.1
Release:        1.hum1.pigeon
Summary:        Digital VCR and streaming server
License:        GPL-2.0-or-later AND LGPL-2.1-or-later AND MIT AND BSD-3-Clause
URL:            https://ffmpeg.org/
Source0:        https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz

BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: make
BuildRequires: pkgconfig
BuildRequires: yasm
BuildRequires: zlib-devel
BuildRequires: bzip2-devel
BuildRequires: xz-devel
BuildRequires: gmp-devel
BuildRequires: gnutls-devel
BuildRequires: libass-devel
BuildRequires: libbluray-devel
BuildRequires: libdrm-devel
BuildRequires: libvdpau-devel
BuildRequires: libva-devel
BuildRequires: libvorbis-devel
BuildRequires: opus-devel
BuildRequires: speex-devel
BuildRequires: libtheora-devel
BuildRequires: lame-devel
BuildRequires: libvpx-devel
BuildRequires: libwebp-devel
BuildRequires: xz-devel
BuildRequires: zlib-devel
BuildRequires: pkgconfig(libdrm)
BuildRequires: pkgconfig(xcb)
BuildRequires: pkgconfig(xcb-shm)
BuildRequires: pkgconfig(xcb-xfixes)
BuildRequires: pkgconfig(xcb-shape)
BuildRequires: pkgconfig(xcb-xfixes)
BuildRequires: pulseaudio-libs-devel
%if %{with all_codecs}
BuildRequires: sdl2-devel
BuildRequires: SDL2-devel
%endif
BuildRequires: libva-devel
BuildRequires: libvdpau-devel

Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: ffmpeg-free%{?_isa} = %{version}-%{release}

%description
Digital VCR and streaming server

%package free
Summary: Complete and free FFmpeg build
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: %{name}-free%{?_isa} = %{version}-%{release}
Obsoletes: %{name} < %{version}-%{release}
Provides: %{name} = %{version}-%{release}

%description free
Complete and free FFmpeg build

%prep
%autosetup -n ffmpeg-7.1 -p1

%build
./configure \
  --prefix=%{_prefix} \
  --libdir=%{_libdir} \
  --enable-gpl \
  --enable-version3 \
  --enable-nonfree \
  --enable-shared \
  --disable-static \
  --enable-libass \
  --enable-libfreetype \
  --enable-libvorbis \
  --enable-libopus \
  --enable-libtheora \
  --enable-libvpx \
  --enable-libwebp \
  --enable-libmp3lame \
  --enable-libspeex
# NOTE: no --enable-libx264/--enable-libx265: x264/x265 are RPMFusion-only
# and absent from our buildroots (configure hard-fails without them).

%make_build

%install
%make_install

%package libs
Summary:        FFmpeg runtime libraries
%description libs
FFmpeg runtime libraries.

%files
%license LICENSE
%doc README.md
%{_bindir}/ffmpeg
%{_bindir}/ffprobe
%{_bindir}/ffplay

%files libs
%license LICENSE
%{_libdir}/libav*.so.*
%{_libdir}/libpostproc.so.*
%{_libdir}/libsw*.so.*

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 7.1-1.hum1.pigeon
- Initial Kestrel package (independent recipe)
- Add theora-devel BuildRequires for --enable-libtheora