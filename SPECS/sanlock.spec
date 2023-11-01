Name:           sanlock
Version:        3.8.4
Release:        1%{?dist}
Summary:        A shared storage lock manager

Group:          System Environment/Base
License:        GPLv2 and GPLv2+ and LGPLv2+
URL:            https://pagure.io/sanlock/
BuildRequires:  gcc
BuildRequires:  libaio-devel
BuildRequires:  libblkid-devel
BuildRequires:  libuuid-devel
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  python3-devel
BuildRequires:  systemd-units
Requires:       %{name}-lib = %{version}-%{release}
Requires(pre):  /usr/sbin/groupadd
Requires(pre):  /usr/sbin/useradd
Requires(post): systemd-units
Requires(post): systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
Source0:        https://releases.pagure.org/sanlock/%{name}-%{version}.tar.gz

%global python_package python3-%{name}

%description
The sanlock daemon manages leases for applications on hosts using shared storage.

%prep
%setup -q

%build
# upstream does not require configure
# upstream does not support _smp_mflags
CFLAGS=$RPM_OPT_FLAGS make -C wdmd
CFLAGS=$RPM_OPT_FLAGS make -C src
CFLAGS=$RPM_OPT_FLAGS make -C python PY_VERSION=3.6
CFLAGS=$RPM_OPT_FLAGS make -C reset

%install
rm -rf $RPM_BUILD_ROOT
make -C src \
        install LIBDIR=%{_libdir} \
        DESTDIR=$RPM_BUILD_ROOT
make -C wdmd \
        install LIBDIR=%{_libdir} \
        DESTDIR=$RPM_BUILD_ROOT
make -C python \
        install LIBDIR=%{_libdir} \
        DESTDIR=$RPM_BUILD_ROOT \
        PY_VERSION=3.6
make -C reset \
        install LIBDIR=%{_libdir} \
        DESTDIR=$RPM_BUILD_ROOT


install -D -m 0644 init.d/sanlock.service.native $RPM_BUILD_ROOT/%{_unitdir}/sanlock.service
install -D -m 0755 init.d/wdmd $RPM_BUILD_ROOT/usr/lib/systemd/systemd-wdmd
install -D -m 0644 init.d/wdmd.service.native $RPM_BUILD_ROOT/%{_unitdir}/wdmd.service
install -D -m 0644 init.d/sanlk-resetd.service $RPM_BUILD_ROOT/%{_unitdir}/sanlk-resetd.service

install -D -m 0644 src/logrotate.sanlock \
    $RPM_BUILD_ROOT/etc/logrotate.d/sanlock

install -D -m 0644 src/sanlock.conf \
    $RPM_BUILD_ROOT/etc/sanlock/sanlock.conf

install -D -m 0644 init.d/wdmd.sysconfig \
    $RPM_BUILD_ROOT/etc/sysconfig/wdmd

install -Dd -m 0755 $RPM_BUILD_ROOT/etc/wdmd.d
install -Dd -m 0775 $RPM_BUILD_ROOT/%{_rundir}/sanlock
install -Dd -m 0775 $RPM_BUILD_ROOT/%{_rundir}/sanlk-resetd

%pre
getent group sanlock > /dev/null || /usr/sbin/groupadd \
    -g 179 sanlock
getent passwd sanlock > /dev/null || /usr/sbin/useradd \
    -u 179 -c "sanlock" -s /sbin/nologin -r \
    -g 179 -d /run/sanlock sanlock
/usr/sbin/usermod -a -G disk sanlock

%post
%systemd_post wdmd.service sanlock.service

%preun
%systemd_preun wdmd.service sanlock.service

%postun
%systemd_postun

%files
/usr/lib/systemd/systemd-wdmd
%{_unitdir}/sanlock.service
%{_unitdir}/wdmd.service
%{_sbindir}/sanlock
%{_sbindir}/wdmd
%dir %{_sysconfdir}/wdmd.d
%dir %{_sysconfdir}/sanlock
%dir %attr(-,sanlock,sanlock) %{_rundir}/sanlock
%{_mandir}/man8/wdmd*
%{_mandir}/man8/sanlock*
%config(noreplace) %{_sysconfdir}/logrotate.d/sanlock
%config(noreplace) %{_sysconfdir}/sanlock/sanlock.conf
%config(noreplace) %{_sysconfdir}/sysconfig/wdmd
%doc init.d/sanlock
%doc init.d/sanlock.service
%doc init.d/wdmd.service

%package        lib
Summary:        A shared storage lock manager library
Group:          System Environment/Libraries

%description    lib
The %{name}-lib package contains the runtime libraries for sanlock,
a shared storage lock manager.
Hosts connected to a common SAN can use this to synchronize their
access to the shared disks.

%ldconfig_scriptlets lib

%files          lib
%{_libdir}/libsanlock.so.*
%{_libdir}/libsanlock_client.so.*
%{_libdir}/libwdmd.so.*

%package        -n %{python_package}
Summary:        Python bindings for the sanlock library
Group:          Development/Libraries
Requires:       %{name}-lib = %{version}-%{release}

%description    -n %{python_package}
The %{python_package} package contains a module that permits applications
written in the Python programming language to use the interface
supplied by the sanlock library.

%files          -n %{python_package}
%{python3_sitearch}/sanlock_python-*.egg-info
%{python3_sitearch}/sanlock*.so

%package        devel
Summary:        Development files for %{name}
Group:          Development/Libraries
Requires:       %{name}-lib = %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%files          devel
%{_libdir}/libwdmd.so
%{_includedir}/wdmd.h
%{_libdir}/libsanlock.so
%{_libdir}/libsanlock_client.so
%{_includedir}/sanlock.h
%{_includedir}/sanlock_rv.h
%{_includedir}/sanlock_admin.h
%{_includedir}/sanlock_resource.h
%{_includedir}/sanlock_direct.h
%{_libdir}/pkgconfig/libsanlock.pc
%{_libdir}/pkgconfig/libsanlock_client.pc

%package -n     sanlk-reset
Summary:        Host reset daemon and client using sanlock
Group:          System Environment/Base
Requires:       sanlock = %{version}-%{release}
Requires:       sanlock-lib = %{version}-%{release}

%description -n sanlk-reset
The sanlk-reset package contains the reset daemon and client.
A cooperating host running the daemon can be reset by a host
running the client, so long as both maintain access to a
common sanlock lockspace.

%files -n       sanlk-reset
%{_sbindir}/sanlk-reset
%{_sbindir}/sanlk-resetd
%{_unitdir}/sanlk-resetd.service
%dir %attr(-,root,root) %{_rundir}/sanlk-resetd
%{_mandir}/man8/sanlk-reset*


%changelog
* Tue Jun 01 2021 David Teigland <teigland@redhat.com> 3.8.4-1
- Update to sanlock-3.8.4

* Thu May 20 2021 David Teigland <teigland@redhat.com> 3.8.3-2
- Fix connection close and add python inquire api

* Tue Jan 19 2021 David Teigland <teigland@redhat.com> 3.8.3-1
- Update to sanlock-3.8.3

* Mon Aug 10 2020 David Teigland <teigland@redhat.com> 3.8.2-1
- Update to sanlock-3.8.2

* Thu Jul 09 2020 David Teigland <teigland@redhat.com> 3.8.1-1
- Update to sanlock-3.8.1

* Wed Jun 12 2019 Nir Soffer <nsoffer@redhat.com> 3.8.0-2
- kick the gating tests to run

* Wed Jun 12 2019 Nir Soffer <nsoffer@redhat.com> 3.8.0-1
- Cleanup spec and convert to python3

* Thu Dec 06 2018 David Teigland <teigland@redhat.com> - 3.6.0-5
- Fix selinux lockfile error

* Thu Oct 04 2018 David Teigland <teigland@redhat.com> - 3.6.0-4
- makefile gcc flags

* Tue Jun 12 2018 Charalampos Stratakis <cstratak@redhat.com> - 3.6.0-3
- Conditionalize the python2 subpackage

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Dec 12 2017 David Teigland <teigland@redhat.com> - 3.6.0-1
- Update to sanlock-3.6.0, drop fence_sanlock

* Sun Aug 20 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 3.5.0-6
- Add Provides for the old name without %%_isa

* Sun Aug 20 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 3.5.0-5
- Add Provides for the old name without %%_isa

* Sat Aug 19 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 3.5.0-4
- Python 2 binary package renamed to python2-sanlock
  See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon May 01 2017 David Teigland <teigland@redhat.com> - 3.5.0-1
- Update to sanlock-3.5.0

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.4.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Fri Jun 10 2016 David Teigland <teigland@redhat.com> - 3.4.0-1
- Update to sanlock-3.4.0

* Tue Feb 23 2016 David Teigland <teigland@redhat.com> - 3.3.0-2
- remove exclusive arch

* Mon Feb 22 2016 David Teigland <teigland@redhat.com> - 3.3.0-1
- Update to sanlock-3.3.0

* Tue Dec 01 2015 David Teigland <teigland@redhat.com> - 3.2.4-2
- wdmd: prevent probe while watchdog is used

* Fri Jun 19 2015 David Teigland <teigland@redhat.com> - 3.2.4-1
- Update to sanlock-3.2.4

* Fri May 22 2015 David Teigland <teigland@redhat.com> - 3.2.3-2
- add pkgconfig files

* Wed May 20 2015 David Teigland <teigland@redhat.com> - 3.2.3-1
- Update to sanlock-3.2.3

* Thu Oct 30 2014 David Teigland <teigland@redhat.com> - 3.2.2-2
- checksum endian fix

* Mon Sep 29 2014 David Teigland <teigland@redhat.com> - 3.2.2-1
- Update to sanlock-3.2.2

* Thu Aug 21 2014 David Teigland <teigland@redhat.com> - 3.2.1-1
- Update to sanlock-3.2.1

* Mon Aug 18 2014 David Teigland <teigland@redhat.com> - 3.2.0-1
- Update to sanlock-3.2.0

* Wed Jan 29 2014 David Teigland <teigland@redhat.com> - 3.1.0-2
- version interface

* Tue Jan 07 2014 David Teigland <teigland@redhat.com> - 3.1.0-1
- Update to sanlock-3.1.0

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 3.0.1-3
- Mass rebuild 2013-12-27

* Thu Aug 01 2013 David Teigland <teigland@redhat.com> - 3.0.1-2
- use /usr/lib instead of /lib

* Wed Jul 31 2013 David Teigland <teigland@redhat.com> - 3.0.1-1
- Update to sanlock-3.0.1

* Wed Jul 24 2013 David Teigland <teigland@redhat.com> - 3.0.0-1
- Update to sanlock-3.0.0

