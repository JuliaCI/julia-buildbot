###############################################################################
# Define everything needed to build nightly Julia with threading enabled
###############################################################################

julia_threading_builders = ["nightly_threading-x86", "nightly_threading-x64"]
threading_nightly_scheduler = Nightly(name="Julia Threading package", builderNames=julia_threading_builders, hour=[1,13], branch="master", onlyIfChanged=True )
c['schedulers'].append(threading_nightly_scheduler)

for arch in ["x86", "x64"]:
    force_scheduler = ForceScheduler(
        name="Julia Threading building",
        builderNames=["nightly_threading-%s" % arch],
        reason=FixedParameter(name="reason", default=""),
        branch=FixedParameter(name="branch", default=""),
        repository=FixedParameter(name="repository", default=""),
        project=FixedParameter(name="project", default="Juno"),
        properties=[])
    c['schedulers'].append(force_scheduler)

julia_threading_factory = BuildFactory()
julia_threading_factory.useProgress = True
julia_threading_factory.addSteps([
    # Clone julia
    Git(
    	name="Julia checkout",
    	repourl=Property('repository', default='git://github.com/JuliaLang/julia.git'),
    	mode='incremental',
    	method='clean',
    	submodules=True,
    	clobberOnFailure=True,
    	progress=True
    ),
    # Fetch so that remote branches get updated as well.
    ShellCommand(
    	name="git fetch",
    	command=["git", "fetch"],
    	flunkOnFailure=False
    ),

    # Add our particular configuration to flags
    SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", Interpolate("%(prop:flags)s JULIA_THREADS=1")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]
    ),

    # Make!
    ShellCommand(
        name="make binary-dist",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s binary-dist")],
        haltOnFailure = True
    ),

    # Test!
    ShellCommand(
    	name="make testall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s testall")]
    ),

    SetPropertyFromCommand(
        name="Get major/minor version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor)\")"],
        property="majmin"
    ),
    SetPropertyFromCommand(
        name="Get major/minor/patch version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor).$(VERSION.patch)\")"],
        property="version"
    ),
    SetPropertyFromCommand(
        name="Get shortcommit",
        command=["./julia", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
        property="shortcommit"
    ),

    # Upload the result!
    MasterShellCommand(
        name="mkdir julia_package",
        command=["mkdir", "-p", "/tmp/julia_package"]
    ),
    FileUpload(
        slavesrc=Interpolate("julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz"),
        masterdest=Interpolate("/tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")
    ),

    # Upload it to AWS and cleanup the master!
    MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliathreading-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz /tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Upload to AWS (latest)",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/juliathreading-latest-linux%(prop:bits)s.tar.gz /tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
        doStepIf=is_nightly_build,
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", Interpolate("/tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),

    MasterShellCommand(
        name="Report success",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"linux_threading-%(prop:tar_arch)s\", \"url\": \"https://s3.amazonaws.com/julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliathreading-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
        doStepIf=is_nightly_build
    ),
])


for arch in ["x86", "x64"]:
    c['builders'].append(BuilderConfig(
        name="nightly_threading-%s"%(arch),
        slavenames=["ubuntu14.04-%s"%(arch)],
        category="Nightlies",
        factory=julia_threading_factory
    ))
