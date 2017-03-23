@util.renderer
def run_julia_tests(props_obj):
    cmd = ["bin/julia", "-e", "Base.runtests()"]

    if is_windows(props_obj):
        cmd[0] += ".exe"
    return cmd

separated_testing_factory = util.BuildFactory()
separated_testing_factory.useProgress = True
separated_testing_factory.addSteps([
    # Cleanup
    steps.ShellCommand(
        name="Cleanup",
        command=["rm", "-rf", "*"],
    ),

    # Download Julia
    steps.SetPropertyFromCommand(
        name="Download latest Julia",
        command=download_latest_julia,
        property="julia_path",
    ),

    # Run the tests
    steps.SetPropertyFromCommand(
        name="Run tests",
        command=run_julia_tests,
        property="code_result",
    ),
])

# Add our runners on various platforms
separated_runners  = ["separated_tester_osx64", "separated_tester_win32", "separated_tester_win64"]
separated_runners += ["separated_tester_linux%s"%(arch) for arch in ["32", "64", "armv7l", "ppc64le", "aarch64"]]

# Add a manual scheduler for running code snippets
separated_scheduler = schedulers.ForceScheduler(
    name="separated_testing",
    label="Run Julia testing separated from the build environments",
    builderNames=separated_runners,
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Julia"),
        )
    ],
    properties=[
    ]
)
c['schedulers'].append(separated_scheduler)

for builder, worker in builder_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name="separated_tester_" + builder,
        workernames=["tabularasa-" + worker],
        tags=["Testing"],
        factory=separated_testing_factory
    ))
