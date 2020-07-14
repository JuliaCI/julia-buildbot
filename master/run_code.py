@util.renderer
def run_julia(props_obj):
    cmd = ["bin/julia", "command.jl"]

    if is_windows(props_obj):
        cmd[0] += ".exe"
    return cmd


run_code_factory = util.BuildFactory()
run_code_factory.useProgress = True
run_code_factory.addSteps([
    # Cleanup
    steps.ShellCommand(
        name="Cleanup",
        command=["rm", "-rf", "*"],
    ),

    # Download Julia
    steps.ShellCommand(
        name="Download Julia",
        command=download_julia,
    ),

    # Invoke julia on the provided code block
    steps.StringDownload(
        util.Property('code_block'),
        name="Create command.jl",
        workerdest="command.jl",
    ),
    steps.SetPropertyFromCommand(
        name="Run code block",
        command=run_julia,
        property="code_result",
    ),
])

# Add our runners on various platforms
code_runners  = ["runcode_macos64", "runcode_macosaarch64", "runcode_win32", "runcode_win64"]
code_runners += ["runcode_linux%s"%(arch) for arch in ["32", "64", "armv7l", "ppc64le", "aarch64"]] + ["runcode_musl64"]
code_runners += ["runcode_freebsd64"]

# Add a manual scheduler for running code snippets
code_scheduler = schedulers.ForceScheduler(
    name="run_code",
    label="Run arbitrary code block",
    builderNames=code_runners,
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
        util.StringParameter(name="shortcommit", label="shortcommit (e.g. 1a2b3c4d)", size=15, default=""),
        util.StringParameter(name="majmin", label="majmin version (e.g. 0.5)", size=2, default=""),
        util.TextParameter(name="code_block", label="Code to run", default="", cols=80, rows=5),
    ]
)
c['schedulers'].append(code_scheduler)

for builder, workers in builder_mapping.items():
    c['builders'].append(util.BuilderConfig(
        name="runcode_" + builder,
        workernames=["tabularasa_"+w for w in workers],
        tags=["Coderun"],
        collapseRequests=False,
        factory=run_code_factory
    ))
