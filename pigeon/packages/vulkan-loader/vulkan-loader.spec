Name:           vulkan-loader
Version:        1.4.357.0
Release:        %autorelease
Summary:        Vulkan ICD desktop loader

License:        Apache-2.0
URL:            https://github.com/KhronosGroup/Vulkan-Loader
Source0:        %url/archive/vulkan-sdk-%{version}.tar.gz#/Vulkan-Loader-sdk-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  vulkan-headers = %{version}
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-cursor)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(wayland-egl)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xrandr)

Provides:       vulkan%{?_isa} = %{version}-%{release}
Provides:       vulkan = %{version}-%{release}
Obsoletes:      vulkan < %{version}-%{release}
Provides:       vulkan-filesystem = %{version}-%{release}
Obsoletes:      vulkan-filesystem < %{version}-%{release}

Recommends:     mesa-vulkan-drivers%{?_isa}

%description
This project provides the Khronos official Vulkan ICD desktop 
loader for Windows, Linux, and MacOS.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       vulkan-headers
Provides:       vulkan-devel%{?_isa} = %{version}-%{release}
Provides:       vulkan-devel = %{version}-%{release}
Obsoletes:      vulkan-devel < %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.


%prep
%autosetup -p1 -n Vulkan-Loader-vulkan-sdk-%{version}


%build
%cmake -GNinja -DCMAKE_BUILD_TYPE=Release
%cmake_build


%install
%cmake_install

# create the filesystem
mkdir -p %{buildroot}%{_sysconfdir}/vulkan/{explicit,implicit}_layer.d/ \
%{buildroot}%{_datadir}/vulkan/{explicit,implicit}_layer.d/ \
%{buildroot}{%{_sysconfdir},%{_datadir}}/vulkan/icd.d


%ldconfig_scriptlets


%files
%license LICENSE.txt
%doc README.md CONTRIBUTING.md
%dir %{_sysconfdir}/vulkan/
%dir %{_sysconfdir}/vulkan/explicit_layer.d/
%dir %{_sysconfdir}/vulkan/icd.d/
%dir %{_sysconfdir}/vulkan/implicit_layer.d/
%dir %{_datadir}/vulkan/
%dir %{_datadir}/vulkan/explicit_layer.d/
%dir %{_datadir}/vulkan/icd.d/
%dir %{_datadir}/vulkan/implicit_layer.d/
%{_libdir}/*.so.*

%files devel
%{_libdir}/pkgconfig/vulkan.pc
%{_libdir}/*.so
%dir %{_libdir}/cmake/VulkanLoader/
%{_libdir}/cmake/VulkanLoader/*.cmake

%changelog
%autochangelog
