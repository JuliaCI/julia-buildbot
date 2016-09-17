###############################################################################
# Define everything needed to download, sign and reupload juno binaries
###############################################################################

# Add a manual scheduler for signing juno
juno_scheduler = schedulers.ForceScheduler(
    name="juno signing",
    builderNames=["juno_osx10.9-x64", "juno_win6.2-x86", "juno_win6.2-x64"],
    reason=util.FixedParameter(name="reason", default=""),
    branch=util.FixedParameter(name="branch", default=""),
    revision=util.FixedParameter(name="revision", default=""),
    repository=util.FixedParameter(name="repository", default=""),
    project=util.FixedParameter(name="project", default="Juno"),
    properties=[
        util.StringParameter(name="osx64_url", label="OSX 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-mac-x64.dmg"),
        util.StringParameter(name="win32_url", label="Windows 32-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x32.zip"),
        util.StringParameter(name="win64_url", label="Windows 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x64.zip")
    ]
)
c['schedulers'].append(juno_scheduler)

sign_juno_factory = BuildFactory()
sign_juno_factory.useProgress = True
sign_juno_factory.addSteps([
    # Download our sign_juno.sh script over to the slave: (we don't use FileDownload here because of stupid buildbot problems)
    ShellCommand(command=["/usr/bin/curl", "-L", "https://raw.githubusercontent.com/staticfloat/julia-buildbot/master/commands/sign_juno.sh", "-o", "sign_juno.sh"]),

    # Invoke it
    ShellCommand(command=["/bin/bash", "sign_juno.sh", Property('osx64_url'), Property('win32_url'), Property('win64_url')], haltOnFailure=True),

    # Grab the output and transfer it back!
    SetPropertyFromCommand(name="Get filename", command=["/bin/bash", "-c", "ls *-signed*"], property="filename"),
    MasterShellCommand(name="mkdir juno_cache", command=["mkdir", "-p", "/tmp/juno_cache"]),
    FileUpload(slavesrc=Interpolate("%(prop:filename)s"), masterdest=Interpolate("/tmp/juno_cache/%(prop:filename)s")),
    MasterShellCommand(name="Upload to AWS", command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public junolab/latest/signed/%(prop:filename)s /tmp/juno_cache/%(prop:filename)s")], haltOnFailure=True),

    # Cleanup!
    MasterShellCommand(name="Cleanup", command=["rm", "-f", Interpolate("/tmp/bottle_cache/%(prop:filename)s")])
])

for name in ["osx10.9-x64", "win6.2-x86", "win6.2-x64"]:
    c['builders'].append(BuilderConfig(
        name="juno_%s"%(name),
        slavenames=[name],
        category="Juno",
        factory=sign_juno_factory,
    ))
