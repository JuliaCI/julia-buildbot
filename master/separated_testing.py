###############################################################################
# Define everything needed to do per-commit testing.  This is the "separted
# testing" that @staticfloat has been going on about for so many years...
###############################################################################

@util.renderer
def run_julia_tests(props_obj):
    props = props_obj_to_dict(props_obj)
    cmd = ["bin/julia", "-e", "Base.runtests([\"all\"]; ncores=min(Sys.CPU_THREADS, 8))"]

    if is_windows(props_obj):
        cmd[0] += ".exe"
    return cmd

# Steps to download a linux tarball, extract it, run testing on it, and maybe trigger coverage
julia_testing_factory = util.BuildFactory()
julia_testing_factory.useProgress = True
julia_testing_factory.addSteps([
    # Clean the place out from previous runs
    steps.ShellCommand(
        name="clean it out",
        command=["/bin/sh", "-c", "rm -rf *"],
        flunkOnFailure=False,
    ),

    # Download the appropriate tarball and extract it
    steps.ShellCommand(
        name="Download Julia",
        command=download_julia,
    ),

    # Run tests!
    steps.ShellCommand(
        name="Run tests",
        command=run_julia_tests,
        haltOnFailure=True,
    ),

    # Promote from pretesting to a nightly if it worked!
    steps.MasterShellCommand(
        name="Promote on AWS",
        command=render_promotion_command,
        haltOnFailure=True,
    ),
    steps.MasterShellCommand(
        name="Promote on AWS (latest)",
        command=render_latest_promotion_command,
        haltOnFailure=True,
    ),

    # Cleanup AWS
    steps.MasterShellCommand(
        name="Cleanup pretesting",
        command=render_cleanup_pretesting_command,
    ),

    # Trigger coverage build if everything goes well
    steps.Trigger(
        schedulerNames=["Julia Coverage Testing"],
        set_properties={
            'download_url': render_download_url,
            'commitmessage': util.Property('commitmessage'),
            'commitname': util.Property('commitname'),
            'commitemail': util.Property('commitemail'),
            'authorname': util.Property('authorname'),
            'authoremail': util.Property('authoremail'),
            'shortcommit': util.Property('shortcommit'),
        },
        waitForFinish=False,
        doStepIf=should_run_coverage,
    )
])

for builder, worker in builder_mapping.iteritems():
    tester_name = "tester_%s"%(builder)
    # Add a dependent scheduler for running tests after we build tarballs
    c['schedulers'].append(schedulers.Triggerable(
        name="Julia %s Testing"%(builder),
        builderNames=[tester_name],
    ))

    # Add testing builders
    c['builders'].append(util.BuilderConfig(
        name=tester_name,
        workernames=["tabularasa_%s"%(worker)],
        collapseRequests=False,
        tags=["Testing"],
        factory=julia_testing_factory,
    ))


c['schedulers'].append(schedulers.ForceScheduler(
    name="force_test",
    label="Force test build",
    builderNames=["tester_%s"%(k) for k in builder_mapping.keys()],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Coverage"),
        )
    ],
    properties=[
        util.StringParameter(
            name="url",
            size=60,
            default="https://julialangnightlies-s3.julialang.org/bin/linux/x64/julia-latest-linux64.tar.gz"
        ),
    ]
))
