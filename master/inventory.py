###############################################################################
# Define our buildworker inventory, and define attributes for each worker
###############################################################################

def build_names(platform, versions, architectures):
    names = []
    for version in versions:
        for arch in architectures:
            names += ["%s%s-%s"%(platform, version, arch)]
    return names

win_names    = build_names("win", ["6_2"], ["x64", "x86"])
ubuntu_names = build_names("ubuntu", ["14_04"], ["x64", "x86", "arm"])
osx_names    = build_names("osx", ["10_9", "10_10", "10_11"], ["x64"])
centos_names = build_names("centos", ["5_11"], ["x64", "x86"])
# Add some special centos names that don't fit in with the rest
centos_names += ["centos6_7-x64", "centos7_1-x64", "centos7_2-ppc64le"]
all_names    = ubuntu_names + osx_names + centos_names + win_names

# Define all the attributes we'll use in our buildsteps
c['workers'] = []
for name in all_names:
    # Initialize march to none, as some buildbots (power8) don't set it
    march = None

    # Everything should be VERBOSE
    flags = 'VERBOSE=1 '

    # Add on the banner
    flags += 'TAGGED_RELEASE_BANNER="Official http://julialang.org/ release" '

    if name[-3:] == 'x86':
        tar_arch = 'i686'
        march = 'pentium4'
        up_arch = 'x86'
        bits = '32'
        flags += 'JULIA_CPU_TARGET=pentium4 '

    if name[-3:] == 'x64':
        tar_arch = 'x86_64'
        march = 'x86-64'
        up_arch = 'x64'
        bits = '64'

    if name[-3:] == 'arm':
        tar_arch = 'arm'
        march = 'armv7-a'
        up_arch = 'arm'
        bits = 'arm'
        flags += 'JULIA_CPU_TARGET=generic '

    if name[-7:] == 'ppc64le':
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

        # Our OSX builder only devotes 2 cores to each VM
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

    # Construct the actual BuildSlave object
    c['workers'] += [worker.Worker(name, 'julialang42', max_builds=1,
		properties={
			'tar_arch':tar_arch,
			'release':name,
			'flags':flags,
			'up_arch':up_arch,
			'bits':bits
		}
	)]
