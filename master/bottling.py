###############################################################################
# Define everything needed for the bottling of binaries on OSX
###############################################################################

# Steps to build a Homebrew Bottle
osx_bottle_factory = util.BuildFactory()
osx_bottle_factory.useProgress = True
osx_bottle_factory.addSteps([
    # Clean everything out that's in the directory!
    steps.ShellCommand(
    	name="precleanup",
    	command=["/bin/bash", "-c", "rm -f *.{sh,gz}"]
    ),

    # Copy our build_bottle.sh script over to the slave:
    steps.FileDownload(
    	mastersrc="../commands/build_bottle.sh",
    	workerdest="build_bottle.sh"
    ),

    # Next, invoke build_bottle.sh!
    steps.ShellCommand(
    	command=["/bin/bash", "build_bottle.sh", util.Property('formula')],
    	haltOnFailure=True
    ),

    # Grab the output and transfer it back!
    steps.SetPropertyFromCommand(
    	name="Get bottle filename",
    	command=["/bin/bash", "-c", "ls *.tar.gz"],
    	property="filename",
    	haltOnFailure=True
    ),
    steps.MasterShellCommand(
    	name="mkdir bottle_cache",
    	command=["mkdir", "-p", "/tmp/bottle_cache"]
    ),
    steps.FileUpload(
    	workersrc=util.Interpolate("%(prop:filename)s"),
    	masterdest=util.Interpolate("/tmp/bottle_cache/%(prop:filename)s")
    ),
    steps.MasterShellCommand(
    	name="Upload to AWS",
    	command=["/bin/bash", "-c", util.Interpolate("~/bin/aws put --fail --public juliabottles/%(prop:filename)s /tmp/bottle_cache/%(prop:filename)s")],
    	haltOnFailure=True
    ),

    # Cleanup downloaded bottle file
    steps.MasterShellCommand(
    	name="Cleanup",
    	command=["rm", "-f", util.Interpolate("/tmp/bottle_cache/%(prop:filename)s")]
    ),
])

# Add a manual scheduler for building bottles, and ONLY a manual scheduler
c['schedulers'].append(schedulers.ForceScheduler(
    name="force_bottle",
    label="Force bottle building",
    builderNames=["bottle_" + z for z in osx_names],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Bottling"),
        )
    ],
    properties=[
        util.StringParameter(name="formula", label="Formula", size=30, default="staticfloat/juliadeps/")
    ]
))

# Add bottler builders
for name in osx_names:
    c['builders'].append(util.BuilderConfig(
        name="bottle_%s"%(name),
        workernames=[name],
        tags=["Bottling"],
        factory=osx_bottle_factory
    ))
