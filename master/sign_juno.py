###############################################################################
# Define everything needed to download, sign and reupload juno binaries
###############################################################################

# Add a manual scheduler for signing juno
juno_scheduler = ForceScheduler(
    name="juno signing",
    builderNames=["juno_osx10.9", "juno_win8.1-x86", "juno_win8.1-x64"],
    reason=FixedParameter(name="reason", default=""),
    branch=FixedParameter(name="branch", default=""),
    revision=FixedParameter(name="revision", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Juno"),
    properties=[
        StringParameter(name="osx64_url", label="OSX 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-mac-x64.dmg"),
        StringParameter(name="win32_url", label="Windows 32-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x32.zip"),
        StringParameter(name="win64_url", label="Windows 64-bit URL", size=30, default="https://junolab.s3.amazonaws.com/latest/juno-windows-x64.zip")
    ]
)
c['schedulers'].append(juno_scheduler)

sign_juno_factory = BuildFactory()
sign_juno_factory.useProgress = True
sign_juno_factory.addSteps([
    # Copy our sign_juno.sh script over to the slave:
    FileDownload(mastersrc="../commands/sign_juno.sh", slavedest="sign_juno.sh"),

    # Invoke it
    ShellCommand(command=["/bin/bash", "sign_juno.sh", Property('osx64_url'), Property('win32_url'), Property('win64_url')], haltOnFailure=True),

    # Grab the output and transfer it back!
    SetPropertyFromCommand(name="Get filename", command=["/bin/bash", "-c", "ls *-signed*"], property="filename"),
    MasterShellCommand(name="mkdir juno_cache", command=["mkdir", "-p", "/tmp/juno_cache"]),
    FileUpload(slavesrc=Interpolate("%(prop:filename)s"), masterdest=Interpolate("/tmp/juno_cache/%(prop:filename)s")),
    MasterShellCommand(name="Upload to AWS", command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public junolab/latest/signed/%(prop:filename)s /tmp/juno_cache/%(prop:filename)s")], haltOnFailure=True),

    # Cleanup!
    MasterShellCommand(name="Cleanup", command=["rm", "-f", Interpolate("/tmp/bottle_cache/%(prop:filename)s")])
])

for name in ["osx10.9", "win8.1-x86", "win8.1-x64"]:
    c['builders'].append(BuilderConfig(
        name="juno_%s"%(name),
        slavenames=[name],
        category="Juno",
        factory=sign_juno_factory,
    ))
