# Add our runners on various platforms
code_runners  = ["runcode_osx64", "runcode_win32", "runcode_win64"]
code_runners += ["runcode_linux%s"%(arch) for arch in ["32", "64", "armv7l", "ppc64le", "aarch64"]]

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
        util.StringParameter(name="bits", label="bits (e.g. 32)", size=2, default=""),
        util.StringParameter(name="majmin", label="Major.Minor version (e.g. 0.5)", size=2, default=""),
    ]
)
c['schedulers'].append(code_scheduler)


@util.renderer
def download_julia(props_obj):
    # Use munge_artifact_filename() to calculate upload_filename for us
    munge_artifact_filename(props_obj)

    # Use upload_filename to get our download_url
    download_url = gen_download_url(props_obj)

    # Build commands to download/install julia
    if is_mac(props_obj):
        cmd  = "curl -L '%s' -o Julia.dmg && "
        cmd += "hdiutil mount Julia.dmg && "
        cmd += "cp -Ra /Volumes/Julia/*.app/Contents/Resources/julia . && "
        cmd += "hdiutil unmount Julia.dmg"
    elif is_windows(props_obj):
        # TODO: Figure out how to actually do this.  :P
        cmd = "curl -L '%s' -o Julia.exe;"
    else:
        cmd = "curl -L '%s' | tar zxf --strip-components=1"
    return ["/bin/bash", "-c", cmd]


@util.renderer
def run_julia(props_obj):
    cmd = ["bin/julia", "command.jl"]

    if is_windows(props_obj):
        cmd[0] += ".exe"
    return cmd


run_code_factory = util.BuildFactory()
run_code_factory.useProgress = True
run_code_factory.addSteps([
    # First, download Julia
    steps.SetPropertyFromCommand(
        name="Download Julia",
        command=download_julia,
        property="julia_path",
    ),

    # Invoke julia on the provided code block
    steps.StringDownload(
        util.getProperty('code_block'),
        name="Create command.jl",
        workerdest="command.jl",
    ),
    steps.SetPropertyFromCommand(
        name="Run code block",
        command=run_julia,
        property="code_result",
    ),

    # Cleanup
    steps.ShellCommand(
        name="Cleanup",
        command=["rm", "-rf", "*"],
    ),
])


# Map each builder to each worker
mapping = {
    "runcode_osx64": "osx10_10-x64",
    "runcode_win32": "win6_2-x86",
    "runcode_win64": "win6_2-x64",
    "runcode_linux32": "centos5_11-x86",
    "runcode_linux64": "centos5_11-x64",
    "runcode_linuxarmv7l": "debian7_11-armv7l",
    "runcode_linuxppc64le": "debian8_6-ppc64le",
    "runcode_linuxaarch64": "debian8_6-aarch64",
}
for packager, slave in mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=[slave],
        tags=["Coderun"],
        factory=run_code_factory
    ))
