%global uvcommit %{libuvcommit}
%global uvversion 0.11.26

%global Rmathjuliaversion 0.1
%global Rmathversion 3.0.1

%global llvm_version 3.7
%global llvmversion 37

Name:           julia
Version:        %{juliaversion}
Release:        0.%{datecommit}%{?dist}
Summary:        High-level, high-performance dynamic language for technical computing
Group:          Development/Languages
# Julia itself is MIT, with a few LGPLv2+ and GPLv2+ files
# libuv is MIT
# Rmath is  GPLv2+
License:        MIT and LGPLv2+ and GPLv2+
URL:            http://julialang.org/
# These URLs are bogus, just here to help rpmbuild to find the needed files
Source0:        https://api.github.com/repos/JuliaLang/julia/tarball/master#/julia.tar.gz
# Julia currently uses a custom version of libuv, patches are not yet upstream
Source1:        https://api.github.com/repos/JuliaLang/libuv/tarball/%{uvcommit}#/libuv-%{uvcommit}.tar.gz
# Julia currently uses a custom version of Rmath, called Rmath-julia, with a custom RNG system (temporary)
Source2:        https://api.github.com/repos/JuliaLang/Rmath-julia/tarball/v%{Rmathjuliaversion}#/Rmath-julia-%{Rmathjuliaversion}.tar.gz
Provides:       bundled(libuv) = %{uvversion}
Provides:       bundled(Rmath) = %{Rmathversion}
BuildRequires:  arpack-devel
BuildRequires:  desktop-file-utils
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  devtoolset-2-binutils
BuildRequires:  devtoolset-2-build
BuildRequires:  devtoolset-2-gcc
BuildRequires:  devtoolset-2-gcc-c++
%endif
BuildRequires:  dSFMT-devel
BuildRequires:  fftw-devel >= 3.3.2
# Needed to test package management until the switch to libgit2
BuildRequires:  git
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  gmp5-devel >= 5.0
%else
BuildRequires:  gmp-devel >= 5.0
%endif
BuildRequires:  ImageMagick
%if 0%{?rhel} && 0%{?rhel} == 6
BuildRequires:  libgit2-devel >= 1:0.21
%else
BuildRequires:  libgit2-devel >= 0.21
%endif
BuildRequires:  libunwind-devel
BuildRequires:  llvm%{llvmversion}-devel
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  mpfr3-devel >= 3.0
%else
BuildRequires:  mpfr-devel >= 3.0
%endif
BuildRequires:  openblas-threads
%ifarch %{ix86} x86_64
BuildRequires:  openlibm-devel >= 0.4
%endif
BuildRequires:  openspecfun-devel >= 0.4
BuildRequires:  pcre2-devel
BuildRequires:  perl
BuildRequires:  suitesparse-devel
BuildRequires:  utf8proc-devel >= 1.3
BuildRequires:  zlib-devel
# Dependencies loaded at run time by Julia code
# and thus not detected by find-requires
Requires:       arpack
Requires:       dSFMT
Requires:       fftw >= 3.3.2
# Needed for package management until the switch  to libgit2
Requires:       git
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       gmp5 >= 5.0
%else
Requires:       gmp >= 5.0
%endif
Requires:       julia-common = %{version}-%{release}
%if 0%{?rhel} && 0%{?rhel} == 6
Requires:       libgit2 >= 1:0.21
%else
Requires:       libgit2 >= 0.21
%endif
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       mpfr3 >= 3.0
%else
Requires:       mpfr >= 3.0
%endif
Requires:       openblas-threads
%ifarch %{ix86} x86_64
Requires:       openlibm >= 0.4
%endif
Requires:       openspecfun >= 0.4
Requires:       pcre2
# Currently, Julia does not work properly architectures other than x86
# https://bugzilla.redhat.com/show_bug.cgi?id=1158024
# https://bugzilla.redhat.com/show_bug.cgi?id=1158026
# https://bugzilla.redhat.com/show_bug.cgi?id=1158025
ExclusiveArch:  %{ix86} x86_64
%if 0%{?rhel} && 0%{?rhel} <= 5
%global buildroot %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%global _datarootdir %{_datadir}
BuildRoot:      %{buildroot}
%endif

%description
Julia is a high-level, high-performance dynamic programming language
for technical computing, with syntax that is familiar to users of
other technical computing environments. It provides a sophisticated
compiler, distributed parallel execution, numerical accuracy, and an
extensive mathematical function library. The library, largely written
in Julia itself, also integrates mature, best-of-breed C and Fortran
libraries for linear algebra, random number generation, signal processing,
and string processing.

This package only contains the essential parts of the Julia environment:
the julia executable and the standard library.

%package common
Summary:        Julia architecture-independent files
Group:          Development/Languages
%if !(0%{?rhel} && 0%{?rhel} <= 5)
BuildArch:      noarch
%endif
Requires:       julia = %{version}-%{release}

%description common
Contains architecture-independent files required to run Julia.

%package doc
Summary:        Julia documentation and code examples
Group:          Documentation
%if !(0%{?rhel} && 0%{?rhel} <= 5)
BuildArch:      noarch
%endif
Requires:       julia = %{version}-%{release}

%description doc
Contains the Julia manual, the reference documentation of the standard library
and code examples.

%package devel
Summary:        Julia development, debugging and testing files
Group:          Development/Libraries
Requires:       julia%{?_isa} = %{version}-%{release}

%description devel
Contains library symbolic links and header files for developing applications
linking to the Julia library, in particular embedding it, as well as
tests and a debugging version of Julia. This package is normally not
needed when programming in the Julia language, but rather for embedding
Julia into external programs or debugging Julia itself.

%prep
%setup -qn %{name}

mkdir -p deps/srccache

pushd deps/srccache
    # Julia downloads tarballs for external dependencies even when the folder is present:
    # we need to copy the tarball and let the build process unpack it
    # https://github.com/JuliaLang/julia/pull/10280
    cp -p %SOURCE1 .
    cp -p %SOURCE2 .
popd

# Required so that the image is not optimized for the build CPU
# (i386 does not work yet: https://github.com/JuliaLang/julia/issues/7185)
# Without specifying MARCH, the Julia system image would only work on native CPU
%ifarch %{ix86}
%global march pentium4
%endif
%ifarch x86_64
%global march x86-64
%endif
%ifarch %{arm}
# gcc and LLVM do not support the same targets
%global march $(echo %optflags | grep -Po 'march=\\K[^ ]*')
%endif
%ifarch armv7hl
%global march $(echo %optflags | grep -Po 'march=\\K[^ ]*')
%endif
%ifarch aarch64
%global march armv8-a
%endif

%global blas USE_BLAS64=0 LIBBLAS=-lopenblasp LIBBLASNAME=libopenblasp.so.0 LIBLAPACK=-lopenblasp LIBLAPACKNAME=libopenblasp.so.0

%ifarch %{ix86} x86_64
%global libm USE_SYSTEM_LIBM=0 USE_SYSTEM_OPENLIBM=1
%else
%global libm USE_SYSTEM_LIBM=1
%endif

# About build, build_libdir and build_bindir, see https://github.com/JuliaLang/julia/issues/5063#issuecomment-32628111
%global julia_builddir %{_builddir}/%{name}/build
%global commonopts USE_SYSTEM_LLVM=1 USE_LLVM_SHLIB=1 LLVM_CONFIG=llvm-config-%{__isa_bits}-%{llvm_version} USE_SYSTEM_LIBUNWIND=1 USE_SYSTEM_READLINE=1 USE_SYSTEM_PCRE=1 USE_SYSTEM_OPENSPECFUN=1 USE_SYSTEM_BLAS=1 USE_SYSTEM_LAPACK=1 USE_SYSTEM_FFTW=1 USE_SYSTEM_GMP=1 USE_SYSTEM_MPFR=1 USE_SYSTEM_ARPACK=1 USE_SYSTEM_SUITESPARSE=1 USE_SYSTEM_ZLIB=1 USE_SYSTEM_GRISU=1 USE_SYSTEM_DSFMT=1 USE_SYSTEM_LIBUV=0 USE_SYSTEM_RMATH=0 USE_SYSTEM_UTF8PROC=1 USE_SYSTEM_LIBGIT2=1 USE_SYSTEM_PATCHELF=1 VERBOSE=1 MARCH=%{march} %{blas} %{libm} prefix=%{_prefix} bindir=%{_bindir} libdir=%{_libdir} libexecdir=%{_libexecdir} datarootdir=%{_datarootdir} includedir=%{_includedir} sysconfdir=%{_sysconfdir} build_prefix=%{julia_builddir} build_bindir=%{julia_builddir}%{_bindir} build_libdir=%{julia_builddir}%{_libdir} build_private_libdir=%{julia_builddir}%{_libdir}/julia build_libexecdir=%{julia_builddir}%{_libexecdir} build_datarootdir=%{julia_builddir}%{_datarootdir} build_includedir=%{julia_builddir}%{_includedir} build_sysconfdir=%{julia_builddir}%{_sysconfdir} JULIA_CPU_CORES=$(echo %{?_smp_mflags} | sed s/-j//)

%build
%if 0%{?rhel} && 0%{?rhel} <= 6
. /opt/rh/devtoolset-2/enable
%endif

# Need to repeat -march here to override i686 from optflags
%global buildflags CFLAGS="%{optflags} -march=%{march}" CXXFLAGS="%{optflags} -march=%{march}"

make %{?_smp_mflags} %{buildflags} %{commonopts} release
# If debug is not built here, it is built during make install
# And both targets cannot be on the same call currently:
# https://github.com/JuliaLang/julia/issues/10088
make %{?_smp_mflags} %{buildflags} %{commonopts} debug

%check
make %{commonopts} test

%install
make %{commonopts} DESTDIR=%{buildroot} install

cp -p CONTRIBUTING.md LICENSE.md NEWS.md README.md %{buildroot}%{_docdir}/julia/

pushd %{buildroot}%{_prefix}/share/man/man1/
    ln -s julia.1.gz julia-debug.1.gz
popd

# Install .desktop file and icons
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/scalable/apps/
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/16x16/apps/
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/24x24/apps/
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/32x32/apps/
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/48x48/apps/
mkdir -p %{buildroot}%{_datarootdir}/icons/hicolor/256x256/apps/
cp -p doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/scalable/apps/%{name}.svg
convert -scale 16x16 -extent 16x16 -gravity center -background transparent \
    doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/16x16/apps/%{name}.png
convert -scale 24x24 -extent 24x24 -gravity center -background transparent \
    doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/24x24/apps/%{name}.png
convert -scale 32x32 -extent 32x32 -gravity center -background transparent \
    doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/32x32/apps/%{name}.png
convert -scale 48x48 -extent 48x48 -gravity center -background transparent \
    doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/48x48/apps/%{name}.png
convert -scale 256x256 -extent 256x256 -gravity center -background transparent \
    doc/_build/html/_static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/256x256/apps/%{name}.png
desktop-file-validate %{buildroot}%{_datarootdir}/applications/%{name}.desktop

%files
%dir %{_docdir}/julia/
%{_docdir}/julia/LICENSE.md
%doc %{_docdir}/julia/CONTRIBUTING.md
%doc %{_docdir}/julia/NEWS.md
%doc %{_docdir}/julia/README.md
%{_bindir}/julia
%{_libdir}/julia/
%exclude %{_libdir}/julia/libjulia-debug.so
%{_mandir}/man1/julia.1*
%{_datarootdir}/appdata/julia.appdata.xml
%{_datarootdir}/applications/%{name}.desktop
%{_datarootdir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datarootdir}/icons/hicolor/16x16/apps/%{name}.png
%{_datarootdir}/icons/hicolor/24x24/apps/%{name}.png
%{_datarootdir}/icons/hicolor/32x32/apps/%{name}.png
%{_datarootdir}/icons/hicolor/48x48/apps/%{name}.png
%{_datarootdir}/icons/hicolor/256x256/apps/%{name}.png

%files common
%dir %{_datarootdir}/julia/
%{_datarootdir}/julia/*.jl
%{_datarootdir}/julia/base/

%dir %{_sysconfdir}/julia/
%config(noreplace) %{_sysconfdir}/julia/juliarc.jl

%files doc
%doc %{_docdir}/julia/

%files devel
%{_bindir}/julia-debug
%{_libdir}/julia/libjulia-debug.so
%{_includedir}/julia/
%{_datarootdir}/julia/test/
%{_mandir}/man1/julia-debug.1*

%post
/sbin/ldconfig
# Julia currently needs the unversioned .so files:
# https://github.com/JuliaLang/julia/issues/6742
ln -sf %{_libdir}/libarpack.so.2 %{_libdir}/julia/libarpack.so
ln -sf %{_libdir}/libcholmod.so.3 %{_libdir}/julia/libcholmod.so
ln -sf %{_libdir}/libdSFMT.so.2 %{_libdir}/julia/libdSFMT.so
# TODO: do something to handle different libgit2 SONAMES
ln -sf %{_libdir}/libgit2.so.23 %{_libdir}/julia/libgit2.so
ln -sf %{_libdir}/libfftw3_threads.so.3 %{_libdir}/julia/libfftw3_threads.so
ln -sf %{_libdir}/libgmp.so.10 %{_libdir}/julia/libgmp.so
ln -sf %{_libdir}/libmpfr.so.4 %{_libdir}/julia/libmpfr.so
ln -sf %{_libdir}/libopenlibm.so.1 %{_libdir}/julia/libopenlibm.so
ln -sf %{_libdir}/libopenspecfun.so.1 %{_libdir}/julia/libopenspecfun.so
ln -sf %{_libdir}/libpcre2-8.so.0 %{_libdir}/julia/libpcre2-8.so
ln -sf %{_libdir}/libumfpack.so.5 %{_libdir}/julia/libumfpack.so
/bin/touch --no-create %{_datarootdir}/icons/hicolor &>/dev/null || :
exit 0

%postun
/sbin/ldconfig
if [ $1 -eq 0 ] ; then
    rm -f %{_libdir}/julia/libarpack.so
    rm -f %{_libdir}/julia/libcholmod.so
    rm -f %{_libdir}/julia/libdSFMT.so
    rm -f %{_libdir}/julia/libgit2.so
    rm -f %{_libdir}/julia/libfftw3_threads.so
    rm -f %{_libdir}/julia/libgmp.so
    rm -f %{_libdir}/julia/libmpfr.so
    rm -f %{_libdir}/julia/libopenlibm.so
    rm -f %{_libdir}/julia/libopenspecfun.so
    rm -f %{_libdir}/julia/libpcre2-8.so
    rm -f %{_libdir}/julia/libumfpack.so
    /bin/touch --no-create %{_datarootdir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datarootdir}/icons/hicolor &>/dev/null || :
fi
exit 0

%posttrans
/usr/bin/gtk-update-icon-cache %{_datarootdir}/icons/hicolor &>/dev/null || :

%changelog
* Tue Jan 5 2016 Orion Poplawski <orion@cora.nwra.com> - 0.4.2-3
- Use proper conditional for __isa_bits tests

* Thu Dec 24 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.2-2
- Use new ILP64 OpenBLAS, suffixed with 64_ (ARPACK and SuiteSparse still use
  the LP64 Atlas).

* Wed Dec 9 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.2-1
- New upstream release.
- Update bundled libuv to latest Julia fork.

* Mon Nov 9 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.1-1
- New upstream release.
- Pass explicitly -march to override default -march=i686 with pentium4.
- Get rid of useless build dependencies.

* Fri Oct 9 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.0-2
- Use LLVM 3.3 to fix bugs and improve compilation performance.
- Run all the tests now that they pass.
- Stop specifying -fsigned-char explicitly, since it is now handled by Julia.
- Refactor architecture checking logic to prepare support for new arches.
- Use upstream .desktop file instead of a custom one.

* Fri Oct 9 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.0-1
- New upstream release.
- Drop patches now included upstream.
- Drop obsolete rm commands.

* Thu Sep 17 2015 Dave Airlie <airlied@redhat.com> 0.4.0-0.4.rc1
- drag in latest upstream 0.4 branch in hope of fixing i686
- drop out some tests on i686
- build against LLVM 3.7

* Fri Sep 11 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.0-0.3.rc1
- New upstream release candidate.
- Drop now useless patch.
- Remove libccalltest.so file installed under /usr/share/.

* Fri Aug 28 2015 Nils Philippsen <nils@redhat.com> - 0.4.0-0.2.20150823git
- rebuild against suitesparse-4.4.5, to work around
  https://github.com/JuliaLang/julia/issues/12841

* Sun Aug 23 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.4.0-0.1.20150823git
- Update to development version 0.4.0 to fix FTBFS.
- Move to PCRE2, libgit2, utf8proc 1.3, and up-to-date libuv fork.
- Preliminary support for ARM.
- patchelf no longer needed when the same paths are passed to 'make' and 'make install'.
- Building Sphynx documentation no longer needed.
- Fix icons to be square.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu Jun 11 2015 Nils Philippsen <nils@redhat.com> - 0.3.7-4
- rebuild for suitesparse-4.4.4

* Fri Apr 10 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.7-3
- Rebuilt for LLVM 3.6.

* Sat Mar 28 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.7-2
- Rebuild for utf8proc ABI break.

* Tue Mar 24 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.7-1
- New upstream release.

* Mon Mar 2 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.6-2
- Fix loading libcholmod, libfftw3_threads and libumfpack.

* Tue Feb 17 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.6-1
- New upstream release.

* Fri Jan 9 2015 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.5-1
- New upstream release.

* Fri Dec 26 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.4-1
- New upstream release.

* Fri Dec 12 2014 Adam Jackson <ajax@redhat.com> 0.3.3-2
- Rebuild for F21 LLVM 3.5 rebase

* Sun Nov 23 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.3-1
- New upstream release.
- Bump libuv to follow upstream.

* Wed Nov 05 2014 Adam Jackson <ajax@redhat.com> 0.3.2-4
- Don't BuildRequire: llvm-static

* Tue Oct 28 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.2-3
- Trigger rebuild to use LLVM 3.5.

* Thu Oct 23 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.2-2
- New upstream release.

* Sun Oct 12 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.1-3
- Fix missing symlinks to libarpack, libpcre, libgmp and libmpfr, which could
  prevent Julia from working correcly if the -devel packages were missing.
- Fix invalid hard-coded reference to /usr/lib64.

* Fri Sep 26 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.1-2
- Add git to dependencies, as it is needed to install packages.

* Mon Sep 22 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.1-1
- New upstream version.
- Depend on openblas-threads instead of openblas.
- Make source URL automatically depend on version.

* Sat Sep 20 2014 Peter Robinson <pbrobinson@fedoraproject.org> 0.3.0-10
- Add dist tag

* Fri Sep 19 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-9
- Use libopenblasp to enable threading.
- Make julia-common depend on julia.

* Fri Sep 19 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-8
- Use versioned OpenBLAS library.so to work without openblas-devel.
- Use LAPACK from OpenBLAS instead of reference implementation.
- Add .desktop file.
- Remove objects.inv feil from HTML documentation.

* Thu Sep 18 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-7
- Fix double inclusion of HTML documentation.
- Improve working directory logic.

* Thu Sep 18 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-6
- Do not remove _sources directory in HTML documentation.
- Make -doc depend on julia to avoid mismatches.

* Wed Sep 17 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-5
- Revert to installing performance suite (needed to run tests).
- Fix double inclusion of some documentation files.
- Move architecture-independent files to a -common subpackage.
- Install HTML documentation instead of .rst files.
- Fix build and install paths.
- Remove dependencies on dSFMT-devel, openlibm-devel and openlibm-devel,
  replacing them with private symbolic links.
- Stop installing libjulia.so to libdir.

* Mon Sep 15 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-4
- Do not install non-functional performance test suite and Makefiles.
- Install documentation to docdir instead of /usr/share/julia/doc.
- Clarify comment about Julia's license.

* Mon Sep 15 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-3
- Remove -xnolibs argument passed by libuv to dtrace (no longer supported
  by systemtap 2.5).

* Fri Sep 5 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-2
- Claim ownership of Julia directories where needed.
- Move libjulia.so to the base package instead of -devel.

* Thu Aug 28 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-1
- New upstream 0.3 final release.
- Set MARCH=pentium4 for 32-bit builds to work on CPUs older than core2.
- Use llvm package instead of requiring llvm3.3.
- Temporarily disable failing backtrace test.

* Sat Jul 26 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.6.rc1
- Add dSFMT-devel to Requires.
- Use versioned tarball names for libuv and Rmath.

* Sun Jul 06 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.5.git
- Bump libuv and libRmath, simplify tarball names.

* Sat Jun 28 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.4.git
- Use system dSFMT instead of bundling it.

* Thu Jun 12 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.3.git
- Use llvm3.3 package when llvm is 3.4 to avoid failures.
- Fixes to support EPEL.

* Sun May 4 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.2.git
- Automatically use the installed LLVM version.
- Mark dSFMT as bundled library and store version in a macro.

* Tue Apr 29 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.0-0.1.git
- New upstream version 0.3.0.
- Switch to LLVM 3.4.
- Drop useless %%exclude.
- Add blank lines between changelog entries.

* Thu Dec 12 2013 Milan Bouchet-Valat <nalimilan@club.fr> - 0.2.0-2
- Make julia a meta-package and move essential parts to julia-base.
- Use %%{ix86} in ExclusiveArch rather than i386.
- Use %%{buildroot}/%%{_prefix}, %%{_sysconfdir}, %%{_libdir} and %%{_mandir}
  instead of hardcoding paths.
- Use glob pattern to match compressed or uncompressed man pages.
- Move %%post and %%postun before %%files.
- Add blank lines between Changelog entries.

* Wed Dec 11 2013 Milan Bouchet-Valat <nalimilan@club.fr> - 0.2.0-1
- Update to upstream version 0.2.0 and use system libraries as much as possible.

* Thu Jun 14 2012 Orion Poplawski <orion@cora.nwra.com> - 0-0.1.giteecafbe656863a6a8ad4969f53eed358ec2e7555
- Initial package
