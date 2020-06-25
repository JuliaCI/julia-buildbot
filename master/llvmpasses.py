julia_llvmpasses_factory = util.BuildFactory()
julia_llvmpasses_factory.useProgress = True
julia_llvmpasses_factory.addSteps([
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

    # Make debug build
    steps.ShellCommand(
        name="make release",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s release")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),

    steps.ShellCommand(
        name="make test/llvmpasses",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C test/llvmpasses -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),
])

c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia test llvmpasses",
    change_filter=util.ChangeFilter(filter_fn=julia_branch_nonskip_filter),
    builderNames=["llvmpasses_linux64"],
    treeStableTimer=1,
))

# Add workers for these jobs
c['builders'].append(util.BuilderConfig(
    name="llvmpasses_linux64",
    workernames=builder_mapping["linux64"],
    collapseRequests=False,
    tags=["Packaging"],
    factory=julia_llvmpasses_factory,
))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="llvmpasses",
    label="Force llvmpasses",
    builderNames=["llvmpasses_linux64"],
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
