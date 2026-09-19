# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/jeremy-rifkin/cpptrace (tag v1.0.4).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           cpptrace
Version:        1.0.4
Release:        1.hum1.pigeon
Summary:        C++ stack trace library
License:        MIT
URL:            https://github.com/jeremy-rifkin/cpptrace
Source0:        https://github.com/jeremy-rifkin/cpptrace/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  pkgconfig
BuildRequires:  elfutils-libelf-devel
BuildRequires:  libdwarf-devel
BuildRequires:  libunwind-devel

%description
cpptrace is a C++ library for generating stack traces. It provides a simple
API for capturing and formatting stack traces, with support for demangling
symbol names and inline assembly.

%prep
%autosetup -n cpptrace-%{version} -p1

%build
%cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DCPPTRACE_BUILD_SHARED=ON
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_libdir}/libcpptrace.so.*
%{_includedir}/cpptrace/

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Development files for cpptrace, including headers and CMake configuration.

%files devel
%license LICENSE
%{_libdir}/libcpptrace.so
%{_libdir}/cmake/cpptrace/
%{_includedir}/cpptrace/

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 1.0.4-1.hum1.pigeon
- Initial Kestrel package for cpptrace