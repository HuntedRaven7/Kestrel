# Local config package (status: local, no upstream — nothing to verify).
# Owns the GDM autologin drop-in. (mango.desktop, Mango defaults, and the
# awww user unit ship elsewhere: mango RPM / image system_files.)

Name:           kestrel-gdm-config
Version:        1
Release:        1.hum1.pigeon
Summary:        Warbler GDM autologin policy
License:        Apache-2.0
URL:            https://github.com/HuntedRaven7/Kestrel
Source0:        10-warbler-autologin.conf

%description
GDM autologin drop-in for Warbler (opt-in kiosk behavior).

%install
install -Dm0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/gdm/custom.conf.d/10-warbler-autologin.conf

%files
%config(noreplace) %{_sysconfdir}/gdm/custom.conf.d/10-warbler-autologin.conf

%changelog
* Thu Sep 17 2026 Kestrel <kestrel@localhost> - 1-1.hum1.pigeon
- Initial Kestrel config package
