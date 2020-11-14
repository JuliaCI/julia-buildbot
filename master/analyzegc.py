# Steps to build a `make binary-dist` tarball that should work on just about every linux ever
julia_analyzegc_factory = util.BuildFactory()
julia_analyzegc_factory.useProgress = True
julia_analyzegc_factory.addSteps([
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
        mode='full',
        method='fresh',
        submodules=True,
        clobberOnFailure=True,
        progress=True,
        retryFetch=True,
        getDescription={'--tags': True},
    ),

    # Install necessary dependencies
    steps.ShellCommand(
        name="install dependencies",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s -C deps install-llvm install-libuv install-utf8proc install-unwind")],
        haltOnFailure = True,
    ),
    
    # Install necessary dependencies
    steps.ShellCommand(
        name="install clang/llvm (1.6+ compat shim)",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s -C src install-analysis-deps")],
        flunkOnFailure=False,
    ),

    # Run clangsa
    steps.ShellCommand(
        name="Run clangsa",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s -C test/clangsa")],
        haltOnFailure = True,
    ),
    
    # Run analyzegc
    steps.ShellCommand(
        name="Run analyzegc",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s -C src analyzegc")],
        haltOnFailure = True,
    ),
])

# This is the CI scheduler, where we build an assert build and test it
c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia GC Analysis",
    change_filter=util.ChangeFilter(filter_fn=julia_branch_nonskip_filter),
    builderNames=["analyzegc_linux64"],
    treeStableTimer=1,
))

# Add workers for these jobs
c['builders'].append(util.BuilderConfig(
    name="analyzegc_linux64",
    workernames=builder_mapping["linux64"],
    collapseRequests=False,
    tags=["Packaging"],
    factory=julia_analyzegc_factory,
))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="analyzegc",
    label="Force GC analysis",
    builderNames=["analyzegc_linux64"],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Packaging"),
        )
    ],
    properties=[
        util.StringParameter(
            name="extra_make_flags",
            label="Extra Make Flags",
            size=30,
            default="",
        ),
    ],
))
