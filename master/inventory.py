###############################################################################
# Define our buildslave inventory, and define attributes for each slave
###############################################################################

from buildbot.buildslave import BuildSlave

ubuntu_names = []
for version in ["14.04", "12.04"]:
    for arch in ["x64", "x86"]:
        ubuntu_names += ["ubuntu%s-%s"%(version, arch)]

osx_names = ["osx10.8-x64", "osx10.9-x64", "osx10.10-x64"]
centos_names = ["centos5.11-x64", "centos5.11-x86", "centos6.7-x64", "centos7.1-x64"]
win_names = ["win6.2-x64", "win6.2-x86"]
all_names = ubuntu_names + osx_names + centos_names + win_names

# This is getting sickening, how many attributes we're defining here
c['slaves'] = []
for name in all_names:
    deb_arch = 'amd64'
    tar_arch = 'x86_64'
    march = 'x86-64'
    up_arch = 'x64'
    bits = '64'

    # Everything should be VERBOSE
    flags = 'VERBOSE=1 '

    # Add on the banner
    flags += 'TAGGED_RELEASE_BANNER="Official http://julialang.org/ release" '

    if name[-3:] == 'x86':
        deb_arch = 'i386'
        tar_arch = 'i686'
        march = 'i686'
        up_arch = 'x86'
        bits = '32'
        flags += 'JULIA_CPU_TARGET=pentium4 '

    # On windows, disable running doc/genstdlib.jl due to julia issue #11727
    # and add XC_HOST dependent on the architecture
    if name[:3] == 'win':
        flags += 'JULIA_ENABLE_DOCBUILD=0 '
        if march == 'i686':
            flags += 'XC_HOST=i686-w64-mingw32 '
        else:
            flags += 'XC_HOST=x86_64-w64-mingw32 '
    #else:
        # We're going to try compiling everything with ccache to speed up buildtimes
        #flags += 'USECCACHE=1 '

    # On OSX, core2 is the minimum MARCH we support
    if name[:3] == "osx":
        march = "core2"

    # On ancient CentOS systems, O_CLOEXEC makes LLVM sad
    # and old cmake has issues linking openssl in libgit2
    if name[:10] == "centos5.11":
        flags += 'DEPS_CXXFLAGS="-DO_CLOEXEC=0" '
        flags += 'CMAKE=cmake28 '

    # Add MARCH to flags
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



