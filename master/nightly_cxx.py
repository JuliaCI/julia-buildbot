###############################################################################
# Define everything needed to build nightly Julia builds against LLVM SVN for Cxx.jl
###############################################################################

julia_cxx_builders = ["nightly_cxx64"]
cxx_nightly_scheduler = Nightly(name="Julia Cxx package", builderNames=julia_cxx_builders, hour=[0,12], branch="master", onlyIfChanged=True )
c['schedulers'].append(cxx_nightly_scheduler)

cxx_force_scheduler = ForceScheduler(
    name="Julia Cxx building",
    builderNames=["nightly_cxx64"],
    reason=FixedParameter(name="reason", default=""),
    branch=FixedParameter(name="branch", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Juno"),
    properties=[
    ]
)
c['schedulers'].append(cxx_force_scheduler)

julia_cxx_factory = BuildFactory()
julia_cxx_factory.useProgress = True
julia_cxx_factory.addSteps([
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
        command=["echo", Interpolate("%(prop:flags)s LLVM_VER=svn LLVM_ASSERTIONS=1 BUILD_LLVM_CLANG=1 BUILD_LLDB=1 USE_LLVM_SHLIB=1 LLDB_DISABLE_PYTHON=1")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]
    ),
    ShellCommand(
    	name="make distclean-llvm",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s -C deps distclean-llvm")]
    ),

    # Make!
    ShellCommand(
        name="make binary-dist",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s binary-dist")],
        haltOnFailure = True
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
        masterdest=Interpolate("/tmp/julia_package/juliacxx-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")
    ),

    # Upload it to AWS and cleanup the master!
    MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliacxx-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz /tmp/julia_package/juliacxx-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Upload to AWS (latest)",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/juliacxx-latest-linux%(prop:bits)s.tar.gz /tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
        doStepIf=is_nightly_build,
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", Interpolate("/tmp/julia_package/juliacxx-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),

    MasterShellCommand(
        name="Report success",
        command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"linux_cxx-%(prop:tar_arch)s\", \"url\": \"https://s3.amazonaws.com/julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/juliacxx-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
        doStepIf=is_nightly_build
    ),
])


# Add linux tarball builders
#c['builders'].append(BuilderConfig(
#    name="nightly_cxx32",
#    slavenames=["ubuntu12.04-x86"],
#    category="Packaging",
#    factory=julia_cxx_factory
#))

c['builders'].append(BuilderConfig(
    name="nightly_cxx64",
    slavenames=["centos6.7-x64"],
    category="Nightlies",
    factory=julia_cxx_factory
))
