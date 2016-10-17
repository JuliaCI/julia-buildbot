###############################################################################
# Define our buildslave inventory, and define attributes for each slave
###############################################################################

from buildbot.buildslave import BuildSlave

ubuntu_names = []
# Removed 12.04 from this list
for version in ["14.04"]:
    for arch in ["x64", "x86"]:
        ubuntu_names += ["ubuntu%s-%s"%(version, arch)]

osx_names = ["osx10.9-x64", "osx10.10-x64", "osx10.11-x64", "osx10.12-x64"]
centos_names = ["centos5.11-x64", "centos5.11-x86", "centos6.7-x64", "centos7.1-x64", "centos7.2-ppc64le"]
win_names = ["win6.2-x64", "win6.2-x86"]
all_hail_the_nanosoldier = ["nanosoldier-x64"]

# We've got an ubuntu ARM machine!  But don't add him to ubuntu_names, otherwise
# he'll get picked up by quickbuild, and we don't want that
arm_names = ["ubuntu14.04-arm"]

all_names = ubuntu_names + osx_names + centos_names + win_names + all_hail_the_nanosoldier + arm_names

# This is getting sickening, how many attributes we're defining here
c['slaves'] = []
for name in all_names:
    # Initialize march to none, as some buildbots (power8) don't set it
    march = None
   
    # Everything should be VERBOSE
    flags = 'VERBOSE=1 '

    # Add on the banner
    flags += 'TAGGED_RELEASE_BANNER="Official http://julialang.org/ release" '

    if name[-3:] == 'x86':
        deb_arch = 'i386'
        tar_arch = 'i686'
        march = 'pentium4'
        up_arch = 'x86'
        bits = '32'
        flags += 'JULIA_CPU_TARGET=pentium4 '
        # Parallel make
        #flags += '-j3 '

    if name[-3:] == 'x64':
        deb_arch = 'amd64'
        tar_arch = 'x86_64'
        march = 'x86-64'
        up_arch = 'x64'
        bits = '64'
        # Parallel make seems crashy during bootstrap
        #flags += '-j4 '

    if name[-3:] == 'arm':
        deb_arch = 'armhf'
        tar_arch = 'arm'
        march = 'armv7-a'
        up_arch = 'arm'
        bits = 'arm'
        flags += 'JULIA_CPU_TARGET=generic'
        # Add Link-Time-Optimization to ARM builder to work around this GCC bug:
        # https://github.com/JuliaLang/julia/issues/14550
        flags += 'CPPFLAGS=-fLTO LDFLAGS=-fLTO '

    if name[-7:] == 'ppc64le':
        deb_arch = 'ppc64el'
        tar_arch = 'powerpc64le'
        up_arch = 'ppc64le'
        bits = 'ppc64'
        flags += 'JULIA_CPU_TARGET=pwr8 '

    # On windows, disable running doc/genstdlib.jl due to julia issue #11727
    # and add XC_HOST dependent on the architecture
    if name[:3] == 'win':
        flags += 'JULIA_ENABLE_DOCBUILD=0 '
        if march == 'x86-64':
            flags += 'XC_HOST=x86_64-w64-mingw32 '
        else:
            flags += 'XC_HOST=i686-w64-mingw32 '

    # On OSX, core2 is the minimum MARCH we support
    if name[:3] == "osx":
        march = "core2"

        # Just so that we can pass tests on our memory-limited OSX builder,
        # we will set JULIA_CPU_CORES=2, which is sad but apparently necessary.
        flags += 'JULIA_CPU_CORES=2 '
    else:
        flags += 'JULIA_CPU_CORES=4 '

    # tests are hitting memory issues, so restart workers when memory consumption gets too high
    flags += 'JULIA_TEST_MAXRSS_MB=600 '

    # On ancient CentOS systems, O_CLOEXEC makes LLVM sad
    # and old cmake has issues linking openssl in libgit2
    if name[:10] == "centos5.11":
        flags += 'DEPS_CXXFLAGS="-DO_CLOEXEC=0" '
        flags += 'CMAKE=cmake28 '
        # use old c++ abi https://github.com/JuliaLang/julia/issues/17446
        flags += 'CXXFLAGS=-D_GLIBCXX_USE_CXX11_ABI=0 '

    # Add MARCH to flags
    if march != None:
        flags += "MARCH=%s "%(march)
    c['slaves'] += [BuildSlave(name, 'julialang42', max_builds=1,
		properties={
			'deb_arch':deb_arch,
			'tar_arch':tar_arch,
			'release':name,
			'flags':flags,
			'up_arch':up_arch,
			'bits':bits
		}
	)]
