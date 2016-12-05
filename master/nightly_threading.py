###############################################################################
# Define everything needed to build nightly Julia with threading enabled
###############################################################################

julia_threading_builders = ["nightly_threading-x86", "nightly_threading-x64"]
threading_nightly_scheduler = schedulers.Nightly(name="Julia Threading package", builderNames=julia_threading_builders, hour=[1,13], change_filter=util.ChangeFilter(project=['JuliaLang/julia','staticfloat/julia'], branch='master'), onlyIfChanged=True )
c['schedulers'].append(threading_nightly_scheduler)

for arch in ["x86", "x64"]:
    force_scheduler = schedulers.ForceScheduler(
        name="force_thread_%s"%(arch),
        label="Force Julia %s Threading building"%(arch),
        builderNames=["nightly_threading-%s" % arch],
        reason=util.FixedParameter(name="reason", default=""),
        codebases=[
            util.CodebaseParameter(
                "",
                name="",
                branch=util.FixedParameter(name="branch", default=""),
                repository=util.FixedParameter(name="repository", default=""),
                project=util.FixedParameter(name="project", default=""),
            )
        ],
        properties=[])
    c['schedulers'].append(force_scheduler)

julia_threading_factory = util.BuildFactory()
julia_threading_factory.useProgress = True
julia_threading_factory.addSteps([
    # Clone julia
    steps.Git(
    	name="Julia checkout",
    	repourl=util.Property('repository', default='git://github.com/JuliaLang/julia.git'),
    	mode='incremental',
    	method='clean',
    	submodules=True,
    	clobberOnFailure=True,
    	progress=True
    ),
    # Fetch so that remote branches get updated as well.
    steps.ShellCommand(
    	name="git fetch",
    	command=["git", "fetch"],
    	flunkOnFailure=False
    ),

    # Add our particular configuration to flags
    # Enable 4 threads by default
    steps.SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", util.Interpolate("%(prop:flags)s JULIA_THREADS=4")],
        property="flags"
    ),

    # make clean first
    steps.ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s cleanall")]
    ),

    # Make!
    steps.ShellCommand(
        name="make binary-dist",
        command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s binary-dist")],
        haltOnFailure = True
    ),

    # Test!
    steps.ShellCommand(
    	name="make testall",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s testall")]
    ),

    steps.SetPropertyFromCommand(
        name="Get major/minor version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor)\")"],
        property="majmin"
    ),
    steps.SetPropertyFromCommand(
        name="Get major/minor/patch version",
        command=["./julia", "-e", "println(\"$(VERSION.major).$(VERSION.minor).$(VERSION.patch)\")"],
        property="version"
    ),
    steps.SetPropertyFromCommand(
        name="Get shortcommit",
        command=["./julia", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
        property="shortcommit"
    ),

    # Upload the result!
#    steps.MasterShellCommand(
#        name="mkdir julia_package",
#        command=["mkdir", "-p", "/tmp/julia_package"]
#    ),
#    steps.FileUpload(
#        workersrc=util.Interpolate("julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz"),
#        masterdest=util.Interpolate("/tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")
#    ),

    # Upload it to AWS and cleanup the master!
#    steps.MasterShellCommand(
#        name="Upload to AWS",
#        command=["/bin/bash", "-c", util.Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliathreading-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz /tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
#        haltOnFailure=True
#    ),
#    steps.MasterShellCommand(
#        name="Upload to AWS (latest)",
#        command=["/bin/bash", "-c", util.Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/juliathreading-latest-linux%(prop:bits)s.tar.gz /tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
#        doStepIf=is_nightly_build,
#        haltOnFailure=True
#    ),
    steps.MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", util.Interpolate("/tmp/julia_package/juliathreading-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),

#    steps.MasterShellCommand(
#        name="Report success",
#        command=["/bin/bash", "-c", util.Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"linux_threading-%(prop:tar_arch)s\", \"url\": \"https://s3.amazonaws.com/julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliathreading-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
#        doStepIf=is_nightly_build
#    ),
])


for arch in ["x86", "x64"]:
    c['builders'].append(util.BuilderConfig(
        name="nightly_threading-%s"%(arch),
        workernames=["ubuntu14_04-%s"%(arch)],
        tags=["Nightlies"],
        factory=julia_threading_factory
    ))
