###############################################################################
# Define everything needed to download, sign and reupload juno binaries
###############################################################################

sign_juno_factory = util.BuildFactory()
sign_juno_factory.useProgress = True
sign_juno_factory.addSteps([
    # Download our sign_juno.sh script over to the slave: (we don't use steps.FileDownload here because of stupid buildbot problems)
    steps.ShellCommand(command=["/usr/bin/curl", "-L", "https://raw.githubusercontent.com/JuliaCI/julia-buildbot/master/commands/sign_juno.sh", "-o", "sign_juno.sh"]),

    # Invoke it
    steps.ShellCommand(command=["/bin/bash", "sign_juno.sh", util.Property('osx64_url'), util.Property('win32_url'), util.Property('win64_url')], haltOnFailure=True),

    # Grab the output and transfer it back!
    steps.SetPropertyFromCommand(name="Get filename", command=["/bin/bash", "-c", "ls *-signed*"], property="filename"),
    steps.MasterShellCommand(name="mkdir juno_cache", command=["mkdir", "-p", "/tmp/juno_cache"]),
    steps.FileUpload(workersrc=util.Interpolate("%(prop:filename)s"), masterdest=util.Interpolate("/tmp/juno_cache/%(prop:filename)s")),
    steps.MasterShellCommand(name="Upload to AWS", command=["/bin/bash", "-c", util.Interpolate("aws s3 cp --acl public-read /tmp/juno_cache/%(prop:filename)s s3://junolab/latest/signed/%(prop:filename)s")], haltOnFailure=True),

    # Cleanup!
    steps.MasterShellCommand(name="Cleanup", command=["rm", "-f", util.Interpolate("/tmp/juno_cache/%(prop:filename)s")])
])

# Add a manual scheduler for signing juno
juno_scheduler = schedulers.ForceScheduler(
    name="force_juno",
    label="Force juno signing",
    builderNames=["juno_osx10_10-x64", "juno_win10_0-x86", "juno_win10_0-x64"],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Juno"),
        )
    ],
    properties=[
        util.StringParameter(name="osx64_url", label="OSX 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-mac-x64.dmg"),
        util.StringParameter(name="win32_url", label="Windows 32-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x32.zip"),
        util.StringParameter(name="win64_url", label="Windows 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x64.zip")
    ]
)
c['schedulers'].append(juno_scheduler)

for name in ["osx10_10-x64", "win10_0-x86", "win10_0-x64"]:
    c['builders'].append(util.BuilderConfig(
        name="juno_%s"%(name),
        workernames=[name],
        tags=["Juno"],
        factory=sign_juno_factory,
    ))
