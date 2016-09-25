###############################################################################
# Define everything needed to build nightly Julia for noinline test
###############################################################################

noinline_nightly_scheduler = Nightly(name="Julia Noinline Build", builderNames=["nightly_noinline-x64"], hour=[3], branch="master", onlyIfChanged=True)
c['schedulers'].append(noinline_nightly_scheduler)

arch = "x64"
force_scheduler = ForceScheduler(
    name="Julia %s Noinline building"%(arch),
    builderNames=["nightly_noinline-%s" % arch],
    reason=FixedParameter(name="reason", default=""),
    branch=FixedParameter(name="branch", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Juno"),
    properties=[])
c['schedulers'].append(force_scheduler)

julia_noinline_factory = BuildFactory()
julia_noinline_factory.useProgress = True
julia_noinline_factory.addSteps([
    # Clone julia
    Git(
        name="Julia checkout",
        repourl=Property('repository', default='git://github.com/JuliaLang/julia.git'),
        mode='incremental',
        method='clean',
        submodules=True,
        clobberOnFailure=True,
        progress=True
    ),
    # Fetch so that remote branches get updated as well.
    ShellCommand(
        name="git fetch",
        command=["git", "fetch"],
        flunkOnFailure=False
    ),

    # Add our particular configuration to flags
    SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", Interpolate("%(prop:flags)s")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    ShellCommand(
        name="make cleanall",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]
    ),

    # Make!
    ShellCommand(
        name="make",
        command=["/bin/bash", "-c", Interpolate("make -j3 %(prop:flags)s")],
        haltOnFailure = True
    ),

    # Test!
    ShellCommand(
        name="make testall",
        command=["usr/bin/julia", "--inline=no", "--check-bounds=yes",
                 "--startup-file=no", "test/runtests.jl", "all"],
        timeout=7200,
        env={'JULIA_TEST_EXEFLAGS': '--inline=no --check-bounds=yes --startup-file=no --depwarn=error'}
    )
])

c['builders'].append(BuilderConfig(
    name="nightly_noinline-%s"%(arch),
    slavenames=["centos7.1-%s"%(arch)],
    category="Nightlies",
    factory=julia_noinline_factory
))
