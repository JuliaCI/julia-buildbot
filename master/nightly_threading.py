###############################################################################
# Define everything needed to build nightly Julia with threading enabled
###############################################################################

for arch in ["linux64", "linux32", "linuxaarch64"]:
    force_scheduler = schedulers.ForceScheduler(
        name="force_thread_%s"%(arch),
        label="Force Julia %s Threading building"%(arch),
        builderNames=["nightly_threading-%s"%(arch)],
        reason=util.FixedParameter(name="reason", default=""),
        codebases=[
            util.CodebaseParameter(
                "",
                name="",
                branch=util.FixedParameter(name="branch", default=""),
                repository=util.FixedParameter(name="repository", default=""),
                project=util.FixedParameter(name="project", default=""),
            )
        ],
        properties=[])
    c['schedulers'].append(force_scheduler)

julia_threading_factory = util.BuildFactory()
julia_threading_factory.useProgress = True
julia_threading_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present)
    steps.ShellCommand(
        name="git fetch",
        command=["git", "fetch", "--tags", "--all", "--force"],
        flunkOnFailure=False
    ),

    # Clone julia
    steps.Git(
        name="Julia checkout",
        repourl=util.Property('repository', default='git://github.com/JuliaLang/julia.git'),
        mode='incremental',
        method='clean',
        submodules=True,
        clobberOnFailure=True,
        progress=True
    ),
    # Fetch so that remote branches get updated as well.
    steps.ShellCommand(
        name="git fetch",
        command=["git", "fetch"],
        flunkOnFailure=False
    ),

    # Add our particular configuration to flags
    # Enable 4 threads by default
    steps.SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", util.Interpolate("%(prop:flags)s JULIA_THREADS=4")],
        property="flags"
    ),

    # make clean first
    steps.ShellCommand(
        name="make cleanall",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s cleanall")]
    ),

    # Make!
    steps.ShellCommand(
        name="make binary-dist",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s binary-dist")],
        haltOnFailure = True
    ),

    # Test!
    steps.ShellCommand(
        name="make testall",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s testall")]
    ),

    steps.SetPropertyFromCommand(
        name="Get major/minor version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor)\")"],
        property="majmin"
    ),
    steps.SetPropertyFromCommand(
        name="Get major/minor/patch version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor).$(VERSION.patch)\")"],
        property="version"
    ),
    steps.SetPropertyFromCommand(
        name="Get shortcommit",
        command=["./julia", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
        property="shortcommit"
    ),

    steps.MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", util.Interpolate("/tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),
])

threading_nightly_scheduler = schedulers.Nightly(
    name="Julia Threading package",
    builderNames=[
        "nightly_threading-linux32",
        "nightly_threading-linux64",
        "nightly_threading-linuxaarch64",
    ],
    hour=[1,13],
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia'],
        branch='master'
    ),
    onlyIfChanged=True
)
c['schedulers'].append(threading_nightly_scheduler)

for arch in ["linux64", "linux32", "linuxaarch64"]:
    c['builders'].append(util.BuilderConfig(
        name="nightly_threading-%s"%(arch),
        workernames=builder_mapping[arch],
        tags=["Nightlies"],
        factory=julia_threading_factory
    ))
