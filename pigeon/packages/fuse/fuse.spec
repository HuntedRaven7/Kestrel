# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/libfuse/libfuse (tag fuse-2.9.9).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

Name:		fuse
Version:	2.9.9
Release:	26.hum1.pigeon
Summary:	File System in Userspace (FUSE) v2 utilities
License:	GPL-1.0-or-later
URL:		https://github.com/libfuse/libfuse/
Source0:	https://github.com/libfuse/libfuse/releases/download/fuse-2.9.9/fuse-2.9.9.tar.gz

Patch1: fuse2-0001-More-parentheses.patch
Patch2: fuse2-0002-add-fix-for-namespace-conflict-in-fuse_kernel.h.patch
Patch3: fuse2-0003-make-buffer-size-match-kernel-max-transfer-size.patch
Patch4: fuse2-0004-Whitelist-SMB2-found-on-some-NAS-devices.patch
Patch5: fuse2-0005-Whitelist-UFSD-backport-to-2.9-branch-452.patch
Patch6: fuse2-0006-Correct-errno-comparison-571.patch
Patch7: fuse2-0007-util-ulockmgr_server.c-conditionally-define-closefro.patch

Requires:	which
Conflicts:	filesystem < 3
BuildRequires:	libselinux-devel
BuildRequires:	autoconf, automake, libtool, gettext-devel, make
BuildRequires:  systemd-udev
Requires:       fuse-common >= 3.4.2-4

%description
With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains the FUSE v2 userspace tools to
mount a FUSE filesystem.

%package libs
Summary:	File System in Userspace (FUSE) v2 libraries
License:	LGPL-2.1-or-later
Conflicts:	filesystem < 3

%description libs
With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains the FUSE v2 libraries.

%package devel
Summary:	File System in Userspace (FUSE) v2 devel files
Requires:	%{name}-libs = %{version}-%{release}
Requires:	pkgconfig
License:	LGPL-2.1-or-later
Conflicts:	filesystem < 3

%description devel
With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains development files (headers,
pkg-config) to develop FUSE v2 based applications/filesystems.

%prep
%autosetup -p 1 -n fuse-2.9.9

export ACLOCAL_PATH=/usr/share/gettext/m4/
autoreconf -ivf

%build
export MOUNT_FUSE_PATH="%{_sbindir}"
CFLAGS="%{optflags} -D_GNU_SOURCE" %configure
make %{?_smp_mflags}

%install
mkdir -p %{buildroot}/%{_libdir}/pkgconfig
install -m 0755 lib/.libs/libfuse.so.%{version} %{buildroot}/%{_libdir}
install -m 0755 lib/.libs/libulockmgr.so.1.0.1 %{buildroot}/%{_libdir}
install -p fuse.pc %{buildroot}/%{_libdir}/pkgconfig/

%files
%license COPYING
%{_bindir}/*
%{_sbindir}/*

%files libs
%license COPYING
%{_libdir}/libfuse.so.*
%{_libdir}/libulockmgr.so.*

%files devel
%license COPYING
%{_libdir}/libfuse.so
%{_libdir}/pkgconfig/fuse.pc
%{_includedir}/fuse.h

%changelog
* Thu Sep 18 2026 Kestrel <kestrel@localhost> - 2.9.9-26.hum1.pigeon
- Initial Kestrel package (independent recipe)