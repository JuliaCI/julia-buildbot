@util.renderer
def download_julia(props_obj):
    # Calculate upload_filename, add to properties, then get download url
    upload_filename = gen_upload_filename(props_obj)
    props_obj.setProperty("upload_filename", upload_filename, "download_julia")
    download_url = gen_download_url(props_obj)
    props_obj.setProperty('download_url', download_url, "download_julia")

    # Build commands to download/install julia
    if is_mac(props_obj):
        cmd  = "curl -L '%s' -o Julia.dmg && "%(download_url)
        cmd += "hdiutil mount Julia.dmg && "
        cmd += "cp -Ra /Volumes/Julia/*.app/Contents/Resources/julia . && "
        cmd += "hdiutil unmount Julia.dmg"
    elif is_windows(props_obj):
        # TODO: Figure out how to actually do this.  :P
        cmd = "curl -L '%s' -o Julia.exe;"%(download_url)
    else:
        cmd = "curl -L '%s' | tar --strip-components=1 -zx"%(download_url)
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
        util.Property('code_block'),
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
        util.StringParameter(name="majmin", label="majmin version (e.g. 0.5)", size=2, default=""),
        util.TextParameter(name="code_block", label="Code to run", default="", cols=80, rows=5),
    ]
)
c['schedulers'].append(code_scheduler)

for builder, worker in builder_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name="runcode_" + builder,
        workernames=[worker],
        tags=["Coderun"],
        factory=run_code_factory
    ))
