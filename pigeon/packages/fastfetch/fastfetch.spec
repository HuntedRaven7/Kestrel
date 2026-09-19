# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/fastfetch-cli/fastfetch (tag 2.66.0).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:           fastfetch
Version:        2.66.0
Release:        2.hum1.pigeon
Summary:        Fast neofetch-like system information tool

License:        MIT
URL:            https://github.com/fastfetch-cli/fastfetch
Source0:        https://github.com/fastfetch-cli/fastfetch/archive/refs/tags/2.66.0/fastfetch-2.66.0.tar.gz

BuildRequires:  cmake
BuildRequires:  python3
BuildRequires:  gcc
BuildRequires:  hwdata-devel
BuildRequires:  wayland-devel
BuildRequires:  libXrandr-devel
BuildRequires:  dconf-devel
BuildRequires:  dbus-devel
BuildRequires:  sqlite-devel
BuildRequires:  ImageMagick-devel
BuildRequires:  zlib-devel
BuildRequires:  libglvnd-devel
BuildRequires:  mesa-libGL-devel
BuildRequires:  glib2-devel
BuildRequires:  ocl-icd-devel
BuildRequires:  rpm-devel
BuildRequires:  libdrm-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  elfutils-libelf-devel
%if "%{_arch}" != "s390x"
BuildRequires:  libddcutil-devel
%endif
BuildRequires:  vulkan-loader-devel
BuildRequires:  chafa-devel
BuildRequires:  yyjson-devel
BuildRequires:  libva-devel
BuildRequires:  libvdpau-devel
BuildRequires:  lua-devel

Recommends:     hwdata
Suggests:       libXrandr
Suggests:       dconf
Suggests:       sqlite-libs
Suggests:       zlib
Suggests:       libglvnd-glx
Suggests:       ImageMagick-libs
Suggests:       glib2
Suggests:       ocl-icd
Suggests:       chafa-libs
Suggests:       libddcutil
Suggests:       libdrm
Suggests:       pulseaudio-libs
Suggests:       elfutils-libelf

Provides:       fastfetch-bash-completion = %{version}-%{release}
Provides:       fastfetch-zsh-completion = %{version}-%{release}
Provides:       fastfetch-fish-completion = %{version}-%{release}
Obsoletes:      fastfetch-bash-completion < 2.31.0-2
Obsoletes:      fastfetch-zsh-completion < 2.31.0-2
Obsoletes:      fastfetch-fish-completion < 2.31.0-2

ExcludeArch:    %{ix86}

%description
fastfetch is a neofetch-like tool for fetching system information and
displaying them in a pretty way.

%prep
%autosetup -n fastfetch-2.66.0

%build
%cmake -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_bindir}/fastfetch
%{_bindir}/flashfetch
%{_datadir}/fastfetch/
%{_datadir}/fish/vendor_completions.d/fastfetch.fish
%{_datadir}/bash-completion/completions/fastfetch
%{_datadir}/zsh/site-functions/_fastfetch
%{_mandir}/man1/fastfetch.1*

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 2.66.0-2.hum1.pigeon
- Initial Kestrel package (independent recipe)