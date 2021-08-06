###############################################################################
# Define our buildworker inventory, and define attributes for each worker
# Worker naming convension: <os>-<arch>-<identifyer>
###############################################################################

import itertools

def build_names(platform, arch, name):
    """
    Apply new worker naming convension, it will replace build_names
    in the future.

    >>> build_names_new('freebsd', ['amd64'], ['foo', 'bar'])
    ['freebsd-amd64-foo', 'freebsd-amd64-bar']
    """
    return list(map(lambda x: '-'.join(x), itertools.product([platform], arch, name)))

# Our windows machines are on AWS
win_names      = build_names("win", ["x86_64", "i686"], ["aws_%d"%(idx) for idx in range(1,4)])

# Our linux (packaging) machines are typically centos, but we just call them `linux`,
# to fit in with the other builders.  Some run on nanosoldier2 at MIT, some run at OSU,
# some run on packet, etc...
linux_names     = []
linux_names    += build_names("linux", ["x86_64"], ["nanosoldier1_1"] + ["nanosoldier%d_%d"%(jdx, idx) for idx in range(1,3) for jdx in (2,4)])
linux_names    += build_names("linux", ["x86_64"], ["amdci6_%d"%(idx) for idx in range(1,4)])
linux_names    += build_names("linux", ["i686"], ["nanosoldier1_1"] + ["nanosoldier3_%d"%(idx) for idx in range(1,3)])
linux_names    += build_names("linux", ["i686"], ["amdci6_%d"%(idx) for idx in range(1,4)])
linux_names    += build_names("linux", ["ppc64le"], ["osu_%d"%(idx) for idx in range(1,4)])
linux_names    += build_names("linux", ["aarch64"], ["aws_%d"%(idx) for idx in range(1,9)])
linux_names    += build_names("linux", ["armv7l"], ["firefly_%d"%(idx) for idx in range(1,4)])
linux_names    += build_names("linux", ["armv7l"], ["rock64_%d"%(idx) for idx in range(1,2)])
musl_names      = build_names("musl", ["x86_64"], ["nureha_1"])
macos_names     = build_names("macos", ["x86_64"], ["macmini", "macmini2", "macmini3"])
macos_names    += build_names("macos", ["x86_64"], ["macmini-x64-%d"%(idx) for idx in range(1,7)])
macos_names    += build_names("macos", ["aarch64"], ["macmini-aarch64-%d"%(idx) for idx in range(1,3)])
freebsd_names   = build_names("freebsd", ["x86_64"], ["amdci6_%d"%(idx) for idx in range(1,4)])
freebsd_names  += build_names("freebsd", ["x86_64"], ["amdci6_%d"%(idx) for idx in range(4,7)])
all_names       = win_names + linux_names + musl_names + macos_names + freebsd_names

# Define all the attributes we'll use in our buildsteps
c['workers'] = []
for name in all_names:
    # Initialize `march` to `None`, as some buildbots (power8) don't set it
    march = None

    # Initialize `mcpu` to `None`, as most buildbots don't set it (only ARM)
    mcpu = None

    # Initialize `llvm_cmake` to `None`, as no buildbots need it except armv7l
    llvm_cmake = None

    # Initialize `make_cmd` to `make`, as that's what it is on all platforms
    # except for FreeBSD, on which it is `gmake`
    make_cmd = "make"

    # Everything should be VERBOSE
    flags = 'VERBOSE=1 '

    # Add on the tagged release banner
    flags += 'TAGGED_RELEASE_BANNER="Official https://julialang.org/ release" '

    # Persist our source cache
    flags += 'SRCCACHE=/tmp/srccache '

    # By default, we use 6 threads, and do NOT set a maxrss limit
    nthreads = 6
    maxrss = None

    # First, set OS-dependent stuff
    if name[:3] == "win":
        os_name = "winnt"
        os_pkg_ext = "exe"

        # OpenBLAS can't deal with avx512 on windows for some reason.
        flags += "OPENBLAS_NO_AVX512=1 "

        # We actually have a lot of cores here, so make use of them.  Maybe
        # that will balance out the INCREDIBLY SLOW I/O SPEEDS.  :sobbing:
        nthreads = 9

    elif name[:5] == "macos":
        os_name = "mac"
        os_pkg_ext = "dmg"

        # Our macmini has fewer cores than we'd like
        nthreads = 5
    elif name[:7] == "freebsd":
        os_name = "freebsd"
        os_pkg_ext = "tar.gz"
        make_cmd = "gmake"
        flags += 'USE_BINARYBUILDER_LIBUV=0 ' # https://github.com/JuliaLang/julia/issues/34627

    elif name[:4] == "musl":
        os_name = "musl"
        os_pkg_ext = "tar.gz"

        # This guy is a gutless wonder at the moment
        nthreads = 3
    else:
        os_name = "linux"
        os_pkg_ext = "tar.gz"

    if os_name in ["win", "freebsd"]:
        # Organize the output to make it clearer later, when using gmake > v4.0
        flags += '--output-sync=target '

    # Use ccache everywhere
    flags += 'USECCACHE=1 '


    if '-i686-' in name:
        tar_arch = 'i686'
        march = 'pentium4'
        up_arch = 'x86'
        bits = '32'

        cpu_targets = [
            'pentium4',
            'sandybridge,-xsaveopt,clone_all',
        ]
        flags += 'JULIA_CPU_TARGET="%s" '%(';'.join(cpu_targets))

    if '-x86_64-' in name or '-amd64-' in name:
        tar_arch = 'x86_64'
        march = 'x86-64'
        up_arch = 'x64'
        bits = '64'

        cpu_targets = [
            'generic',
            'sandybridge,-xsaveopt,clone_all',
            'haswell,-rdrnd,base(1)',
        ]
        flags += 'JULIA_CPU_TARGET="%s" '%(';'.join(cpu_targets))

    if '-armv7l-' in name:
        tar_arch = 'armv7l'
        # Better to set mcpu than march on arm https://github.com/JuliaCI/julia-buildbot/issues/148
        march = 'armv7-a'
        up_arch = 'armv7l'
        bits = 'armv7l'

        # On arm, limit ourselves to 3 threads, since these are wimpy machines
        # and furthermore set ourselves a MAXRSS limit of 900MB
        nthreads = 3
        maxrss = "900"

        # Sysimg multi-versioning!
        cpu_targets = [
            'armv7-a',
            'armv7-a,neon',
            'armv7-a,neon,vfp4',
        ]
        flags += 'JULIA_CPU_TARGET="%s" '%(';'.join(cpu_targets))
        # Force LLVM cmake build to use the armv7 triple instead of armv8 from uname
        # This might not be an actual issue since we are not building clang, but BSTS
        llvm_cmake = '-DLLVM_HOST_TRIPLE=armv7l-unknown-linux-gnueabihf -DLLVM_DEFAULT_TARGET_TRIPLE=armv7l-unknown-linux-gnueabihf'

    if '-ppc64le-' in name:
        tar_arch = 'powerpc64le'
        up_arch = 'ppc64le'
        bits = 'ppc64'
        flags += 'JULIA_CPU_TARGET=pwr8 '

    if '-aarch64-' in name:
        tar_arch = 'aarch64'
        up_arch = 'aarch64'
        bits = 'aarch64'
        march = 'armv8-a'
        # We have a lot of cores and a lot of RAM, use them.
        nthreads = 8
        cpu_targets = [
            # Base target
            'generic',
            # Cortex A57, Example: NVIDIA Jetson TX1, Jetson Nano
            'cortex-a57',
            # Cavium ThunderX2T99, a common server architecture
            'thunderx2t99',
            # Until we're on LLVM 11, 'carmel' as a CPU type doesn't exist, but we can
            # cobble something together that is more or less equivalent:
            #   https://github.com/llvm/llvm-project/commit/0863e94ebd87f4dea7a457c8441979ec4151fedb#diff-e7c1b2c4e39c03a58a53c9ae8e162886R183
            # Note that we only use features defined within Julia itself here:
            #   https://github.com/JuliaLang/julia/blob/adf6d521afd125f2de12a3209b342148d78981c2/src/features_aarch64.h
            # Additionally, yichao asserts that `crc` is not needed.
            'armv8.2-a,crypto,fullfp16,lse,rdm',
        ]
        flags += 'JULIA_CPU_TARGET="%s" '%(';'.join(cpu_targets))

    # Add MARCH to flags
    if not march is None:
        flags += "MARCH=%s "%(march)
    # Add MCPU to flags
    if not mcpu is None:
        flags += "MCPU=%s "%(mcpu)

    # Construct the actual BuildSlave object, and also double up for the tabularasa
    # builders; we add one for each actual builder.
    for worker_name in [name, "tabularasa_"+name]:
        c['workers'] += [worker.Worker(
            # Name and password, much secure (TM)
            worker_name,
            'julialang42',

            # Don't let the same worker do multiple builds at once
            max_builds=1,

            # Set much lower keepalive interval in an attempt to avoid dropped connections
            keepalive_interval=60,

            # Our veritable portfolio of high-value properties
            properties={
                'tar_arch':tar_arch,
                'release':name,
                'flags':flags,
                'nthreads':nthreads,
                'maxrss':maxrss,
                'up_arch':up_arch,
                'bits':bits,
                'llvm_cmake':llvm_cmake,
                'os_name':os_name,
                'os_pkg_ext':os_pkg_ext,
                'make_cmd':make_cmd,
            }
        )]

# Add in tabularasa workers to all_names so that they volunteer for things like
# the auto_reload builders and whatnot.
all_names += ["tabularasa_" + x for x in all_names]

# Build a nicer mapping for us.  This is how we know things like "package_linux64"
# runs on "linux-x86_64-nanosoldier2_1", for instance.
namefilt = lambda arch, names: [n for n in names if arch in n]
builder_mapping = {
    "macos64": namefilt("x86_64", macos_names),
    "macosaarch64": namefilt("aarch64", macos_names),
    "win32": namefilt("i686", win_names),
    "win64": namefilt("x86_64", win_names),
    "linux32": namefilt("i686", linux_names),
    "linux64": namefilt("x86_64", linux_names),
    "linuxarmv7l": namefilt("armv7l", linux_names),
    "linuxppc64le": namefilt("ppc64le", linux_names),
    "linuxaarch64": namefilt("aarch64", linux_names),
    "freebsd64": namefilt("x86_64", freebsd_names),
    "musl64": namefilt("musl", musl_names),
}
