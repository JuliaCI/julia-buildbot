%global uvcommit 5d608abc3c2e9dc37da04030a0e07ba0af5ae57d
%global uvshortcommit %(c=%{uvcommit}; echo ${c:0:7})
%global uvversion 0.11.22

%global Rmathcommit e432b0c4b01c560353412b3f097d179eef5c0ba2
%global Rmathshortcommit %(c=%{Rmathcommit}; echo ${c:0:7})
%global Rmathversion 3.0.1

%global mojibakecommit bc357b276f1fd7124bbb31a4e212a30e57520eee
%global mojibakeshortcommit %(c=%{mojibakecommit}; echo ${c:0:7})


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
Source0:        https://github.com/JuliaLang/julia/archive/master/julia.tar.gz
# Julia currently uses a custom version of libuv, patches are not yet upstream
Source1:        https://github.com/JuliaLang/libuv/archive/%{uvcommit}/archive/libuv.tar.gz
# Julia currently uses a custom version of Rmath, called Rmath-julia, with a custom RNG system (temporary)
Source2:        https://github.com/JuliaLang/Rmath/archive/%{Rmathcommit}/archive/Rmath.tar.gz
# Temporary until utf8proc RPM includes mojibake patches
Source3:        https://github.com/JuliaLang/libmojibake/archive/%{mojibakecommit}/archive/libmojibake.tar.gz
Patch0:         %{name}_juliadoc.patch
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
BuildRequires:  double-conversion-devel >= 1.1.1
BuildRequires:  dSFMT-devel
BuildRequires:  fftw-devel >= 3.3.2
BuildRequires:  gcc-gfortran
# Needed to test package installation
BuildRequires:  git
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  gmp5-devel >= 5.0
%else
BuildRequires:  gmp-devel >= 5.0
%endif
BuildRequires:  ImageMagick
BuildRequires:  libunwind-devel
BuildRequires:  llvm-devel
BuildRequires:  llvm-static
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  mpfr3-devel >= 3.0
%else
BuildRequires:  mpfr-devel >= 3.0
%endif
BuildRequires:  openblas-devel
BuildRequires:  openlibm-devel >= 0.4
BuildRequires:  openspecfun-devel >= 0.4
BuildRequires:  patchelf
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  pcre1-devel >= 8.31
%else
BuildRequires:  pcre-devel >= 8.31
%endif
BuildRequires:  perl
# To build HTML documentation
BuildRequires:  python-pip
BuildRequires:  python-sphinx
BuildRequires:  python-sphinx_rtd_theme
BuildRequires:  suitesparse-devel
BuildRequires:  zlib-devel
# Dependencies loaded at run time by Julia code
# and thus not detected by find-requires
Requires:       arpack
Requires:       dSFMT
Requires:       fftw >= 3.3.2
# Needed for package installation
Requires:       git
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       gmp5 >= 5.0
%else
Requires:       gmp >= 5.0
%endif
Requires:       julia-common = %{version}-%{release}
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       mpfr3 >= 3.0
%else
Requires:       mpfr >= 3.0
%endif
Requires:       openblas-threads
Requires:       openlibm >= 0.4
Requires:       openspecfun >= 0.4
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       pcre1 >= 8.31
%else
Requires:       pcre >= 8.31
%endif
# Currently, Julia does not work properly on non-x86 architectures
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
%patch0 -p 1

# .gitignore files make rpmlint complain
find . -name ".git*" -exec rm {} \;

pushd deps
    tar xzf %SOURCE1
    tar xzf %SOURCE2
    tar xzf %SOURCE3

    # systemtap 2.5 no longer accepts this option
    # https://github.com/joyent/libuv/issues/1478
    sed -i 's/-xnolibs//' libuv/Makefile.in
popd

# Required so that the image is not optimized for the build CPU
# (i386 does not work yet: https://github.com/JuliaLang/julia/issues/7185)
# Without specifying MARCH, the Julia system image would only work on native CPU
%ifarch %ix86
%global march pentium4
%else
%global march x86-64
%endif

# USE_BLAS64=0 means that BLAS was built with 32-bit integers, even if the library is 64 bits
# About build, build_libdir and build_bindir, see https://github.com/JuliaLang/julia/issues/5063#issuecomment-32628111
%global julia_builddir %{_builddir}/%{name}/build
%global commonopts USE_SYSTEM_LLVM=1 USE_SYSTEM_LIBUNWIND=1 USE_SYSTEM_READLINE=1 USE_SYSTEM_PCRE=1 USE_SYSTEM_OPENSPECFUN=1 USE_SYSTEM_LIBM=0 USE_SYSTEM_OPENLIBM=1 USE_SYSTEM_BLAS=1 USE_SYSTEM_LAPACK=1 USE_SYSTEM_FFTW=1 USE_SYSTEM_GMP=1 USE_SYSTEM_MPFR=1 USE_SYSTEM_ARPACK=1 USE_SYSTEM_SUITESPARSE=1 USE_SYSTEM_ZLIB=1 USE_SYSTEM_GRISU=1 USE_SYSTEM_DSFMT=1 USE_SYSTEM_LIBUV=0 USE_SYSTEM_RMATH=0 USE_LLVM_SHLIB=1 USE_SYSTEM_UTF8PROC=0 LIBBLAS=-lopenblasp LIBBLASNAME=libopenblasp.so.0 LIBLAPACK=-lopenblasp LIBLAPACKNAME=libopenblasp.so.0 VERBOSE=1 USE_BLAS64=0 MARCH=%{march} prefix=%{_prefix} bindir=%{_bindir} libdir=%{_libdir} libexecdir=%{_libexecdir} datarootdir=%{_datarootdir} includedir=%{_includedir} sysconfdir=%{_sysconfdir} build_prefix=%{julia_builddir} build_bindir=%{julia_builddir}%{_bindir} build_libdir=%{julia_builddir}%{_libdir} build_private_libdir=%{julia_builddir}%{_libdir}/julia build_libexecdir=%{julia_builddir}%{_libexecdir} build_datarootdir=%{julia_builddir}%{_datarootdir} build_includedir=%{julia_builddir}%{_includedir} build_sysconfdir=%{julia_builddir}%{_sysconfdir}

%build
%if 0%{?rhel} && 0%{?rhel} <= 6
. /opt/rh/devtoolset-2/enable
%endif

make %{?_smp_mflags} CFLAGS="%{optflags}" CXXFLAGS="%{optflags}" FFLAGS="%{optflags}" %commonopts

%if !(0%{?rhel} && 0%{?rhel} <= 6)
make -C doc html
%endif

%check
pushd test
# make all
# Backtrace test fails with LLVM 3.4, disabled for now
# https://github.com/JuliaLang/julia/issues/8099
    make %commonopts core keywordargs numbers strings collections hashing \
         remote iobuffer arrayops reduce reducedim \
         simdloop linalg blas fft dsp sparse bitarray random \
         math functional bigint sorting statistics spawn parallel arpack file \
         resolve suitesparse complex version pollfd mpfr broadcast \
         socket floatapprox priorityqueue readdlm regex float16 combinatorics \
         sysinfo rounding ranges mod2pi euler show lineedit \
         replcompletions repl test goto
popd

%install
make %commonopts DESTDIR=%{buildroot} install

cp -p CONTRIBUTING.md LICENSE.md NEWS.md README.md %{buildroot}%{_docdir}/julia/

%if !(0%{?rhel} && 0%{?rhel} <= 6)
# Install HTML manual and remove unwanted files
# https://github.com/JuliaLang/julia/issues/8378
pushd %{buildroot}%{_docdir}/julia/
    mv %{_builddir}/%{name}/doc/_build/html/ html/
    rm html/.buildinfo html/objects.inv
popd
%endif

pushd %{buildroot}%{_docdir}/julia
    rm -R devdocs/ manual/ stdlib/
popd

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
cp -p doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg \
    %{buildroot}%{_datarootdir}/icons/hicolor/scalable/apps/%{name}.svg
convert -scale 16x16 doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg  \
    %{buildroot}%{_datarootdir}/icons/hicolor/16x16/apps/%{name}.png
convert -scale 24x24 doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg  \
    %{buildroot}%{_datarootdir}/icons/hicolor/24x24/apps/%{name}.png
convert -scale 32x32 doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg  \
    %{buildroot}%{_datarootdir}/icons/hicolor/32x32/apps/%{name}.png
convert -scale 48x48 doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg  \
    %{buildroot}%{_datarootdir}/icons/hicolor/48x48/apps/%{name}.png
convert -scale 256x256 doc/juliadoc/juliadoc/theme/julia/static/julia-logo.svg  \
    %{buildroot}%{_datarootdir}/icons/hicolor/256x256/apps/%{name}.png
mkdir -p %{buildroot}%{_datarootdir}/applications
cat > %{buildroot}%{_datarootdir}/applications/%{name}.desktop << EOF
[Desktop Entry]
Name=Julia
Comment=High-level, high-performance dynamic language for technical computing
Exec=julia
Icon=%{name}
Terminal=true
Type=Application
Categories=Science;Math;
%if 0%{?rhel} && 0%{?rhel} <= 5
Encoding=UTF-8
%endif
EOF
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
%{_datarootdir}/julia/base/
%exclude %{_datarootdir}/julia/base/build.h

%{_datarootdir}/julia/helpdb.jl

%dir %{_sysconfdir}/julia/
%config(noreplace) %{_sysconfdir}/julia/juliarc.jl

%files doc
%doc %{_docdir}/julia/examples/
%if !(0%{?rhel} && 0%{?rhel} <= 6)
%doc %{_docdir}/julia/html/
%endif

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
ln -sf %{_libdir}/libdSFMT.so.2 %{_libdir}/julia/libdSFMT.so
ln -sf %{_libdir}/libgmp.so.10 %{_libdir}/julia/libgmp.so
ln -sf %{_libdir}/libmpfr.so.4 %{_libdir}/julia/libmpfr.so
ln -sf %{_libdir}/libopenlibm.so.1 %{_libdir}/julia/libopenlibm.so
ln -sf %{_libdir}/libopenspecfun.so.1 %{_libdir}/julia/libopenspecfun.so
ln -sf %{_libdir}/libpcre.so.1 %{_libdir}/julia/libpcre.so
/bin/touch --no-create %{_datarootdir}/icons/hicolor &>/dev/null || :
exit 0

%postun
/sbin/ldconfig
if [ $1 -eq 0 ] ; then
    rm -f %{_libdir}/julia/libarpack.so
    rm -f %{_libdir}/julia/libdSFMT.so
    rm -f %{_libdir}/julia/libgmp.so
    rm -f %{_libdir}/julia/libmpfr.so
    rm -f %{_libdir}/julia/libopenlibm.so
    rm -f %{_libdir}/julia/libopenspecfun.so
    rm -f %{_libdir}/julia/libpcre.so
    /bin/touch --no-create %{_datarootdir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datarootdir}/icons/hicolor &>/dev/null || :
fi
exit 0

%posttrans
/usr/bin/gtk-update-icon-cache %{_datarootdir}/icons/hicolor &>/dev/null || :

%changelog
* Sun Oct 12 2014 Milan Bouchet-Valat <nalimilan@club.fr> - 0.3.1-3+copr
- Add support for EPEL5 and 6.

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
