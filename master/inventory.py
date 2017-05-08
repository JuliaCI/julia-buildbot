###############################################################################
# Define our buildworker inventory, and define attributes for each worker
###############################################################################

def build_names(platform, versions, architectures):
    names = []
    for version in versions:
        for arch in architectures:
            names += ["%s%s-%s"%(platform, version, arch)]
    return names

win_names     = build_names("win", ["6_2"], ["x64", "x86"])
ubuntu_names  = build_names("ubuntu", ["16_04"], ["x64", "x86"])
osx_names     = build_names("osx", ["10_10", "10_11", "10_12"], ["x64"])
centos_names  = build_names("centos", ["6_9"], ["x64", "x86"])
centos_names += build_names("centos", ["7_3"], ["x64", "ppc64le", "aarch64"])
debian_names  = ["debian7_11-armv7l"]
all_names     = ubuntu_names + osx_names + centos_names + win_names + debian_names

# Define all the attributes we'll use in our buildsteps
c['workers'] = []
for name in all_names:
    # Initialize march to None, as some buildbots (power8) don't set it
    march = None

    # Initialize llvm_cmake to None, as no buildbots need it except armv7l
    llvm_cmake = None

    # Everything should be VERBOSE
    flags = 'VERBOSE=1 '

    # Add on the tagged release banner
    flags += 'TAGGED_RELEASE_BANNER="Official http://julialang.org/ release" '

    # First, set OS-dependent stuff
    if name[:3] == "win":
        os_name = "winnt"
        os_pkg_ext = "exe"
    elif name[:3] == "osx":
        os_name = "mac"
        os_pkg_ext = "dmg"
    else:
        os_name = "linux"
        os_pkg_ext = "tar.gz"


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

    if name[-6:] == 'armv7l':
        tar_arch = 'armv7l'
        march = 'armv7-a'
        up_arch = 'armv7l'
        bits = 'armv7l'
        flags += 'JULIA_CPU_TARGET=generic '
        # Force LLVM cmake build to use the armv7 triple instead of armv8 from uname
        # This might not be an actual issue since we are not building clang, but BSTS
        llvm_cmake = '-DLLVM_HOST_TRIPLE=armv7l-unknown-linux-gnueabihf -DLLVM_DEFAULT_TARGET_TRIPLE=armv7l-unknown-linux-gnueabihf'

    if name[-7:] == 'ppc64le':
        tar_arch = 'powerpc64le'
        up_arch = 'ppc64le'
        bits = 'ppc64'
        flags += 'JULIA_CPU_TARGET=pwr8 '

    if name[-7:] == 'aarch64':
        tar_arch = 'aarch64'
        up_arch = 'aarch64'
        bits = 'aarch64'
        march = 'armv8-a'
        flags += 'JULIA_CPU_TARGET=generic '
        flags += 'LLVM_VER=3.9.0 '

    # On windows, disable running doc/genstdlib.jl due to julia issue #11727
    # and add XC_HOST dependent on the architecture
    if name[:3] == 'win':
        flags += 'JULIA_ENABLE_DOCBUILD=0 '
        if march == 'x86-64':
            flags += 'XC_HOST=x86_64-w64-mingw32 '
        else:
            flags += 'XC_HOST=i686-w64-mingw32 '


    if name[:3] == "osx":
        # On OSX, core2 is the minimum MARCH we support
        march = "core2"

        # Our OSX builder only devotes 2 cores to each VM
        flags += 'JULIA_CPU_CORES=2 '
    else:
        flags += 'JULIA_CPU_CORES=4 '

    # tests are hitting memory issues, so restart workers when memory consumption gets too high
    flags += 'JULIA_TEST_MAXRSS_MB=600 '

    # Add MARCH to flags
    if not march is None:
        flags += "MARCH=%s "%(march)

    # Construct the actual BuildSlave object
    for worker_name in [name, "tabularasa_"+name]:
        c['workers'] += [worker.Worker(worker_name, 'julialang42', max_builds=1,
            properties={
                'tar_arch':tar_arch,
                'release':name,
                'flags':flags,
                'up_arch':up_arch,
                'bits':bits,
                'llvm_cmake':llvm_cmake,
                'os_name':os_name,
                'os_pkg_ext':os_pkg_ext,
            }
        )]

# Add in tabularasa workers to all_names so that they volunteer for things like
# the auto_reload builders and whatnot.
all_names += ["tabularasa_" + x for x in all_names]

# Build a nicer mapping for us.  This is how we know things like "package_linux64"
# runs on "centos6_9-x64"
builder_mapping = {
    "osx64": "osx10_10-x64",
    "win32": "win6_2-x86",
    "win64": "win6_2-x64",
    "linux32": "centos6_9-x86",
    "linux64": "centos6_9-x64",
    "linuxarmv7l": "debian7_11-armv7l",
    "linuxppc64le": "centos7_3-ppc64le",
    "linuxaarch64": "centos7_3-aarch64",
}
