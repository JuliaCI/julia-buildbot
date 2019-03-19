###############################################################################
# Define everything needed to build nightly Julia for gc debugging
###############################################################################

julia_gc_debug_factory = util.BuildFactory()
julia_gc_debug_factory.useProgress = True
julia_gc_debug_factory.addSteps([
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
    steps.SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", util.Interpolate("%(prop:flags)s WITH_GC_DEBUG_ENV=1")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    steps.ShellCommand(
        name="make cleanall",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s cleanall")]
    ),

    # Make!
    steps.ShellCommand(
        name="make",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j3 %(prop:flags)s")],
        haltOnFailure = True
    ),

    # Test!
    steps.ShellCommand(
        name="make testall",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s testall")]
    )
])

gc_debug_nightly_scheduler = schedulers.Nightly(
    name="Julia GC Debug Build",
    builderNames=[
        "nightly_gc_debug-linux32",
        "nightly_gc_debug-linux64",
        "nightly_gc_debug-linuxaarch64",
    ],
    hour=[3],
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia'],
        branch='master',
    ),
    onlyIfChanged=True,
)
c['schedulers'].append(gc_debug_nightly_scheduler)

for arch in ["linux64", "linux32", "linuxaarch64"]:
    force_scheduler = schedulers.ForceScheduler(
        name="force_gc_%s"%(arch),
        label="Force Julia %s GC debug building"%(arch),
        builderNames=["nightly_gc_debug-%s"%(arch)],
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

for arch in ["linux64", "linux32", "linuxaarch64"]:
    c['builders'].append(util.BuilderConfig(
        name="nightly_gc_debug-%s"%(arch),
        workernames=builder_mapping[arch],
        tags=["Nightlies"],
        factory=julia_gc_debug_factory
    ))
