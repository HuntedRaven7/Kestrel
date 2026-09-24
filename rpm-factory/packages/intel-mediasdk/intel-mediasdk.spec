%undefine __cmake_in_source_build
%global mfx_abi 1
%global mfx_version %{mfx_abi}.35

Summary: Hardware-accelerated video processing on Intel integrated GPUs library
Name: intel-mediasdk
Version: 23.2.2
Release: 12%{?dist}
URL: https://github.com/Intel-Media-SDK/MediaSDK
Source0: %{url}/archive/%{name}-%{version}.tar.gz
# fix build with GCC 13
Patch0: %{name}-gcc13.patch
# gtest 1.17 requires C++17
# Downstream-only because the upstream project is archived
Patch1: %{name}-cpp17.patch
License: MIT
ExclusiveArch: x86_64
BuildRequires: cmake
BuildRequires: gcc-c++
BuildRequires: gmock-devel
BuildRequires: libdrm-devel
BuildRequires: libpciaccess-devel
BuildRequires: libva-devel
BuildRequires: libX11-devel
BuildRequires: ocl-icd-devel
BuildRequires: wayland-devel
Obsoletes: libmfx < %{mfx_version}
Provides: libmfx = %{mfx_version}
Provides: libmfx%{_isa} = %{mfx_version}

%global __provides_exclude_from ^%{_libdir}/mfx/libmfx_.*\\.so$

%description
Intel Media SDK provides a plain C API to access hardware-accelerated video
decode, encode and filtering on Intel Gen graphics hardware platforms.
Implementation written in C++ 11 with parts in C-for-Media (CM).

Supported video encoders: HEVC, AVC, MPEG-2, JPEG, VP9 Supported video decoders:
HEVC, AVC, VP8, VP9, MPEG-2, VC1, JPEG Supported video pre-processing filters:
Color Conversion, Deinterlace, Denoise, Resize, Rotate, Composition

%package devel
Summary: SDK for hardware-accelerated video processing on Intel integrated GPUs
Provides: libmfx-devel = %{mfx_version}
Provides: libmfx%{_isa}-devel = %{mfx_version}
Requires: %{name}%{_isa} = %{version}-%{release}

%description devel
Intel Media SDK provides a plain C API to access hardware-accelerated video
decode, encode and filtering on Intel Gen graphics hardware platforms.
Implementation written in C++ 11 with parts in C-for-Media (CM).

Supported video encoders: HEVC, AVC, MPEG-2, JPEG, VP9 Supported video decoders:
HEVC, AVC, VP8, VP9, MPEG-2, VC1, JPEG Supported video pre-processing filters:
Color Conversion, Deinterlace, Denoise, Resize, Rotate, Composition

%package tracer
Summary: Dump the calls of an application to the Intel Media SDK library
Requires: %{name}%{_isa} = %{version}-%{release}

%description tracer
Media SDK Tracer is a tool which permits to dump logging information from the
calls of the application to the Media SDK library. Trace log obtained from this
tool is a recommended information to provide to Media SDK team on submitting
questions and issues.

%prep
%setup -q -n MediaSDK-%{name}-%{version}
%patch -P0 -p1 -b .gcc13
%patch -P1 -p1 -b .cpp17

%build
%cmake \
    -DBUILD_DISPATCHER=ON \
    -DBUILD_SAMPLES=OFF \
    -DBUILD_TESTS=ON \
    -DBUILD_TOOLS=OFF \
    -DENABLE_OPENCL=ON \
    -DENABLE_WAYLAND=ON \
    -DENABLE_X11=ON \
    -DENABLE_X11_DRI3=ON \
    -DUSE_SYSTEM_GTEST=ON \

%cmake_build

%install
%cmake_install

%check
%cmake_build -- test

%files
%license LICENSE
%doc CHANGELOG.md CONTRIBUTING.md README.rst
%{_libdir}/libmfx.so.%{mfx_abi}
%{_libdir}/libmfx.so.%{mfx_version}
%{_libdir}/libmfxhw64.so.%{mfx_abi}
%{_libdir}/libmfxhw64.so.%{mfx_version}
%dir %{_libdir}/mfx
%{_libdir}/mfx/libmfx_*_hw64.so
%dir %{_datadir}/mfx
%{_datadir}/mfx/plugins.cfg

%files devel
%dir %{_includedir}/mfx
%{_includedir}/mfx/mfx*.h
%{_libdir}/libmfx.so
%{_libdir}/libmfxhw64.so
%{_libdir}/pkgconfig/libmfx.pc
%{_libdir}/pkgconfig/libmfxhw64.pc
%{_libdir}/pkgconfig/mfx.pc

%files tracer
%{_bindir}/mfx-tracer-config
%{_libdir}/libmfx-tracer.so
%{_libdir}/libmfx-tracer.so.%{mfx_abi}
%{_libdir}/libmfx-tracer.so.%{mfx_version}

%changelog
* Thu Jul 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Fri Apr 17 2026 Dominik Mierzejewski <dominik@greysector.net> - 23.2.2-11
- stop using obsolete cmake3 macros
- use patch macro syntax with better backwards compatibility

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Mon Nov 03 2025 Benjamin A. Beasley <code@musicinmybrain.net> - 23.2.2-9
- Build as C++17 for compatibility with gtest 1.17

* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Fri Jan 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Sat Jun 15 2024 Dominik Mierzejewski <dominik@greysector.net> - 23.2.2-5
- add missing directories to owned files list (resolves rhbz#2281591)

* Wed Jan 24 2024 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Jan 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 23.2.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sat Jun 17 2023 Dominik Mierzejewski <dominik@greysector.net> - 23.2.2-1
- update to 23.2.2 (#2193487)
- fix deprecated patchN macro usage

* Wed Apr 19 2023 Dominik Mierzejewski <dominik@greysector.net> - 23.2.0-1
- update to 23.2.0 (#2158351)

* Tue Mar 21 2023 Nicolas Chauvet <kwizart@gmail.com> - 23.1.4-1
- Update to 23.1.4

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 22.6.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Tue Jan 17 2023 Dominik Mierzejewski <dominik@greysector.net> - 22.6.4-2
- fix build with GCC 13

* Wed Dec 28 2022 Nicolas Chauvet <kwizart@gmail.com> - 22.6.4-1
- Update to 22.6.4

* Mon Oct 17 2022 Dominik Mierzejewski <dominik@greysector.net> - 22.5.4-1
- update to 22.5.4 (#2076810)

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 22.4.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Mon Jul 04 2022 Dominik Mierzejewski <dominik@greysector.net> - 22.4.4-1
- update to 22.4.4 (#2076810)

* Wed Mar 16 2022 Dominik Mierzejewski <rpm@greysector.net> - 22.3.0-1
- update to 22.3.0 (#2056132)

* Tue Feb 08 2022 Dominik Mierzejewski <rpm@greysector.net> - 22.1.0-1
- update to 22.1.0 (#2044186)

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 21.4.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Mon Jan 03 2022 Nicolas Chauvet <kwizart@gmail.com> - 21.4.3-1
- Update to 21.4.3

* Sun Oct 03 2021 Nicolas Chauvet <kwizart@gmail.com> - 21.3.5-1
- Update to 21.3.5

* Sat Jul 24 2021 Dominik Mierzejewski <rpm@greysector.net> - 21.2.3-1
- update to 21.2.3 (#1935837)

* Thu Jul 22 2021 Fedora Release Engineering <releng@fedoraproject.org> - 21.1.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Sun Apr 04 2021 Nicolas Chauvet <kwizart@gmail.com> - 21.1.3-1
- Update to 21.1.3

* Thu Feb 18 2021 Dominik Mierzejewski <rpm@greysector.net> - 20.5.1-1
- update to 20.5.1
- drop obsolete patch

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 20.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Oct 30 2020 Dominik Mierzejewski <rpm@greysector.net> - 20.3.1-1
- update to 20.3.1 (#1891948)

* Wed Oct 14 2020 Jeff Law <law@redhat.com> - 20.3.0-2
- Add missing #includes for gcc-11

* Fri Oct 02 2020 Dominik Mierzejewski <rpm@greysector.net> - 20.3.0-1
- update to 20.3.0 (#1884321)

* Fri Aug 07 2020 Dominik Mierzejewski <rpm@greysector.net> - 20.2.1-1
- update to 20.2.1 (#1827296)
- fix build with recent cmake macro changes
- put the new Media SDK Tracer in a separate subpackage

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 20.1.1-3
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 20.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 08 2020 Dominik Mierzejewski <rpm@greysector.net> 20.1.1-1
- update to 20.1.1

* Fri Apr 10 2020 Dominik Mierzejewski <rpm@greysector.net> 20.1.0-1
- update to 20.1.0 (#1786892)

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 19.3.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sat Nov 09 2019 Dominik Mierzejewski <rpm@greysector.net> 19.3.0-2
- Add missing Obsoletes: and Requires:
- Add license text and docs

* Fri Oct 11 2019 Dominik Mierzejewski <rpm@greysector.net> 19.3.0-1
- initial build
