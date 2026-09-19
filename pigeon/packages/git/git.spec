# Kestrel-original recipe (status: independent, not a Fedora dist-git import).
# Upstream: https://github.com/git/git (tag v2.47.0).
# Source0 MUST match pigeon/config/upstream-sources.json (verified by
# source_pipeline.py before any build).

%bcond_without docs
%bcond_without tests

%global gitexecdir          %{_libexecdir}/git-core

%if 0%{?fedora}
%bcond_without              linkcheck
%else
%bcond_with                 linkcheck
%endif

%if 0%{?fedora} >= 38 || 0%{?rhel} >= 10
%bcond_with                 perl_modcompat
%else
%bcond_without              perl_modcompat
%endif

%if 0%{?fedora} || 0%{?rhel} == 9
%bcond_without              asciidoctor
%else
%bcond_with                 asciidoctor
%endif

%if 0%{?fedora} || 0%{?rhel} >= 8
%bcond_with                 python2
%bcond_without              python3
%global gitweb_httpd_conf   gitweb.conf
%global use_glibc_langpacks 1
%global use_perl_generators 1
%global use_perl_interpreter 1
%else
%bcond_without              python2
%bcond_with                 python3
%global build_cflags        %{build_cflags} -fPIC -std=gnu99
%global gitweb_httpd_conf   git.conf
%global use_glibc_langpacks 0
%global use_perl_generators 0
%global use_perl_interpreter 0
%endif

Name:           git
Version:        2.47.0
Release:        1.hum1.pigeon
Summary:        Fast Version Control System
License:        GPL-2.0-only
URL:            https://git-scm.com/
Source0:        https://www.kernel.org/pub/software/scm/git/git-2.47.0.tar.xz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  pkgconfig
BuildRequires:  zlib-devel
BuildRequires:  libcurl-devel
BuildRequires:  openssl-devel
BuildRequires:  expat-devel
BuildRequires:  gettext-devel
BuildRequires:  pcre2-devel
BuildRequires:  perl-generators
BuildRequires:  perl-interpreter
BuildRequires:  perl-generators
BuildRequires:  perl(ExtUtils::MakeMaker)
BuildRequires:  perl(ExtUtils::Embed)
# GCC 16 defines unreachable() macro in stddef.h, conflicts with git's unreachable function
BuildRequires:  sed
%if %{with docs}
BuildRequires: asciidoctor
BuildRequires: xmlto
%endif
%if %{with tests}
BuildRequires: perl(Test::More)
%endif

Requires: perl(:MODULE_COMPAT_%(%{__perl} -e 'print $Config::Config{version}'))
Requires: perl(Error)
Requires: perl(Term::ReadKey)

%description
Git is a fast, scalable, distributed revision control system with an
unusually rich command set that provides both high-level operations
and full access to internals.

%if %{with docs}
%package doc
Summary:        Documentation for %{name}
Requires:       %{name} = %{version}-%{release}
%description doc
Documentation for %{name}.
%endif

%prep
%autosetup -n git-2.47.0

# GCC 16 defines unreachable() macro in stddef.h which conflicts with git's function
# Undefine the macro in the compat header
sed -i '1i #undef unreachable' git-compat-util.h -p1

%build
%make_build \
  CFLAGS="%{build_cflags}" \
  NO_PERL=0 \
  USE_LIBPCRE2=1 \
  INSTALL_SYMLINKS=1

%install
%make_install

%files
%license COPYING
%doc README.md Documentation/
%{_bindir}/git
%{_bindir}/git-*
%{_libexecdir}/git-core/
%{_mandir}/man1/git*.1*
%{_mandir}/man5/git*.5*
%{_mandir}/man7/git*.7*

%changelog
* Fri Sep 18 2026 Kestrel <kestrel@localhost> - 2.47.0-1.hum1.pigeon
- Initial Kestrel package (independent recipe)