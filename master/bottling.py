###############################################################################
# Define everything needed for the bottling of binaries on OSX
###############################################################################

# Add a manual scheduler for building bottles, and ONLY a manual scheduler
c['schedulers'].append(ForceScheduler(
    name="bottle build",
    builderNames=["bottle_" + z for z in osx_names],
    reason=FixedParameter(name="reason", default=""),
    branch=FixedParameter(name="branch", default=""),
    revision=FixedParameter(name="revision", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Bottling"),
    properties=[
        StringParameter(name="formula", label="Formula", size=30, default="staticfloat/juliadeps/")
    ]
))

# Steps to build a Homebrew Bottle
osx_bottle_factory = BuildFactory()
osx_bottle_factory.useProgress = True
osx_bottle_factory.addSteps([
    # Clean everything out that's in the directory!
    ShellCommand(
    	name="precleanup",
    	command=["/bin/bash", "-c", "rm -f *.{sh,gz}"]
    ),
    
    # Copy our build_bottle.sh script over to the slave:
    FileDownload(
    	mastersrc="../commands/build_bottle.sh",
    	slavedest="build_bottle.sh"
    ),
    
    # Next, invoke build_bottle.sh!
    ShellCommand(
    	command=["/bin/bash", "build_bottle.sh", Property('formula')],
    	haltOnFailure=True
    ),

    # Grab the output and transfer it back!
    SetPropertyFromCommand(
    	name="Get bottle filename",
    	command=["/bin/bash", "-c", "ls *.tar.gz"],
    	property="filename",
    	haltOnFailure=True
    ),
    MasterShellCommand(
    	name="mkdir bottle_cache",
    	command=["mkdir", "-p", "/tmp/bottle_cache"]
    ),
    FileUpload(
    	slavesrc=Interpolate("%(prop:filename)s"),
    	masterdest=Interpolate("/tmp/bottle_cache/%(prop:filename)s")
    ),
    MasterShellCommand(
    	name="Upload to AWS",
    	command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public juliabottles/%(prop:filename)s /tmp/bottle_cache/%(prop:filename)s")],
    	haltOnFailure=True
    ),

    # Cleanup downloaded bottle file
    MasterShellCommand(
    	name="Cleanup",
    	command=["rm", "-f", Interpolate("/tmp/bottle_cache/%(prop:filename)s")]
    ),
])

# Add bottler builders
for name in osx_names:
    c['builders'].append(BuilderConfig(
        name="bottle_%s"%(name),
        slavenames=[name],
        category="Bottling",
        factory=osx_bottle_factory
    ))

