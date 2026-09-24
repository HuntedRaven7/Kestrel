%global __python %{__python3}
Name:           vulkan-headers
Version:        1.4.357.0
Release:        %autorelease
Summary:        Vulkan Header files and API registry

License:        Apache-2.0
URL:            https://github.com/KhronosGroup/Vulkan-Headers
Source0:        %url/archive/vulkan-sdk-%{version}.tar.gz#/Vulkan-Headers-sdk-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildArch:      noarch 

%description
Vulkan Header files and API registry

%prep
%autosetup -n Vulkan-Headers-vulkan-sdk-%{version}


%build
%cmake -DCMAKE_INSTALL_LIBDIR=%{_libdir} -GNinja
%cmake_build


%install
%cmake_install


%files
%license LICENSE.md
%doc README.md
%{_includedir}/vulkan/
%{_includedir}/vk_video/
%dir %{_datadir}/vulkan/
%dir %{_datadir}/cmake/VulkanHeaders/
%{_datadir}/vulkan/registry/
%{_datadir}/cmake/VulkanHeaders/*.cmake


%changelog
%autochangelog
