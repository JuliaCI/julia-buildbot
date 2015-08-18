###############################################################################
# Define everything needed to build nightly Julia for gc debugging
###############################################################################

gc_debug_nightly_scheduler = Nightly(name="Julia GC Debug Build", builderNames=["nightly_gc_debug-x86", "nightly_gc_debug-x64"], hour=[3], branch="master", onlyIfChanged=True)
c['schedulers'].append(gc_debug_nightly_scheduler)

julia_gc_debug_factory = BuildFactory()
julia_gc_debug_factory.useProgress = True
julia_gc_debug_factory.addSteps([
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
        command=["echo", Interpolate("%(prop:flags)s WITH_GC_DEBUG_ENV=1")],
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
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s")],
    	haltOnFailure = True
    ),

    # Test!
    ShellCommand(
    	name="make testall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s testall")]
    )
])

for arch in ["x86", "x64"]:
    c['builders'].append(BuilderConfig(
        name="nightly_gc_debug-%s"%(arch),
        slavenames=["ubuntu14.04-%s"%(arch)],
        category="Nightlies",
        factory=julia_gc_debug_factory
    ))
