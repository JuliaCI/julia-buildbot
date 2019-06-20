julia_whitespace_factory = util.BuildFactory()
julia_whitespace_factory.useProgress = True
julia_whitespace_factory.addSteps([
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

    # Check whitespace
    steps.ShellCommand(
        name="make check-whitespace",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s check-whitespace")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
    ),
])

c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia check whitespace",
    change_filter=util.ChangeFilter(filter_fn=julia_ci_filter),
    builderNames=["whitespace_linux32"],
    treeStableTimer=1,
))

# Add workers for these jobs
c['builders'].append(util.BuilderConfig(
    name="whitespace_linux32",
    workernames=builder_mapping["linux32"],
    collapseRequests=False,
    tags=["Packaging"],
    factory=julia_whitespace_factory,
))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="whitespace",
    label="Force whitespace",
    builderNames=["whitespace_linux32"],
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
