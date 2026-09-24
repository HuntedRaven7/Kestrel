# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/jeremy-rifkin/cpptrace (tag v1.0.4).
# Source0 MUST match rpm-factory/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           cpptrace
Version:        1.0.4
Release:        1.hum1.rpmfactory
Summary:        C++ stack trace library
License:        MIT
URL:            https://github.com/jeremy-rifkin/cpptrace
Source0:        https://github.com/jeremy-rifkin/cpptrace/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  pkgconfig
BuildRequires:  elfutils-libelf-devel
BuildRequires:  libdwarf-devel
BuildRequires:  libunwind-devel
BuildRequires:  libzstd-devel

%description
cpptrace is a C++ library for generating stack traces. It provides a simple
API for capturing and formatting stack traces, with support for demangling
symbol names and inline assembly.

%prep
%autosetup -n cpptrace-%{version} -p1

%build
%cmake -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCPPTRACE_BUILD_SHARED=ON \
  -DCPPTRACE_USE_EXTERNAL_LIBDWARF=ON \
  -DCPPTRACE_FIND_LIBDWARF_WITH_PKGCONFIG=ON \
  -DCPPTRACE_USE_EXTERNAL_ZSTD=ON \
  -DCPPTRACE_UNWIND_WITH_LIBUNWIND=ON
# NOTE: autoconfig would pick libgcc _Unwind on Linux, but quickshell's
# crash handler requires CPPTRACE_UNWIND_WITH_LIBUNWIND (signal-safe
# unwinding) and fails its configure check otherwise.
%cmake_build

%install
%cmake_install
# Fix cpptrace-config.cmake to use CONFIG mode for zstd (avoid Findzstd.cmake)
# Also remove libdwarf dependency (libdwarf-devel doesn't provide CMake config)
CONFIG_FILE=%{buildroot}%{_libdir}/cmake/cpptrace/cpptrace-config.cmake
# NOTE: @PACKAGE_INIT@ is already expanded in the installed file, so anchor
# on the literal find_dependency(zstd) line instead (in-place substitution).
sed -i 's/^\(\s*\)find_dependency(zstd)$/\1find_dependency(zstd CONFIG REQUIRED)/' "$CONFIG_FILE"
# Remove the module-path/Findzstd scaffolding around it (line-wise only:
# a range delete would also eat the find_dependency line above)
sed -i '/set(CMAKE_MODULE_PATH_OLD "${CMAKE_MODULE_PATH}")/d' "$CONFIG_FILE"
sed -i '/set(CMAKE_MODULE_PATH "\${CMAKE_MODULE_PATH_OLD}")/d' "$CONFIG_FILE"
sed -i '/unset(CMAKE_MODULE_PATH_OLD)/d' "$CONFIG_FILE"
# Remove libdwarf find_dependency
sed -i '/find_dependency(libdwarf/d' "$CONFIG_FILE"
# Remove the installed Findzstd.cmake
rm -f %{buildroot}%{_libdir}/cmake/cpptrace/Findzstd.cmake

%files
%license LICENSE
%{_libdir}/libcpptrace.so.*
%{_includedir}/cpptrace/
%exclude %{_includedir}/ctrace/
%exclude %{_includedir}/dwarf.h
%exclude %{_includedir}/libdwarf.h
%exclude %{_libdir}/cmake/libdwarf/
%exclude %{_libdir}/cmake/zstd/
%exclude %{_libdir}/libdwarf.a
%exclude %{_libdir}/pkgconfig/libdwarf.pc

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
# cpptrace-config.cmake does find_dependency(zstd CONFIG REQUIRED)
Requires:       libzstd-devel

%description devel
Development files for cpptrace, including headers and CMake configuration.

%files devel
%license LICENSE
%{_libdir}/libcpptrace.so
%{_libdir}/cmake/cpptrace/
%{_includedir}/cpptrace/
%exclude %{_includedir}/ctrace/
%exclude %{_includedir}/dwarf.h
%exclude %{_includedir}/libdwarf.h
%exclude %{_libdir}/cmake/libdwarf/
%exclude %{_libdir}/cmake/zstd/
%exclude %{_libdir}/libdwarf.a
%exclude %{_libdir}/pkgconfig/libdwarf.pc

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.0.4-1.hum1.rpmfactory
- Initial Kestrel package for cpptrace