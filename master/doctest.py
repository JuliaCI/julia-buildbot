julia_doctest_factory = util.BuildFactory()
julia_doctest_factory.useProgress = True
julia_doctest_factory.addSteps([
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

    # Make Julia itself
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
        name="make doctest",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C doc -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s doctest=true")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),

    steps.ShellCommand(
        name="make deploy",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C doc deploy %(prop:flags)s %(prop:extra_make_flags)s")],
        haltOnFailure=True,
        env={
            'DOCUMENTER_KEY': DOCUMENTER_KEY,
            'TRAVIS_PULL_REQUEST': 'false',
        },
        doStepIf=is_protected_branch,
    ),
])

c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia Doctesting",
    change_filter=util.ChangeFilter(filter_fn=julia_ci_filter),
    builderNames=["doctest_linux64"],
    treeStableTimer=1,
))

# Add workers for these jobs
c['builders'].append(util.BuilderConfig(
    name="doctest_linux64",
    workernames=builder_mapping["linux64"],
    collapseRequests=False,
    tags=["Packaging"],
    factory=julia_doctest_factory,
))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="doctest",
    label="Force doctest",
    builderNames=["doctest_linux64"],
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
