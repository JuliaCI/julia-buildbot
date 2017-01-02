###############################################################################
# Define everything needed to build nightly Julia builds against LLVM SVN
###############################################################################

llvmsvn_nightly_scheduler = schedulers.Nightly(name="Julia LLVM SVN Build", builderNames=["nightly_llvmsvn-x86", "nightly_llvmsvn-x64"], hour=[0,12], change_filter=util.ChangeFilter(project=['JuliaLang/julia','staticfloat/julia'], branch='master'), onlyIfChanged=True)
c['schedulers'].append(llvmsvn_nightly_scheduler)

julia_llvmsvn_factory = util.BuildFactory()
julia_llvmsvn_factory.useProgress = True
julia_llvmsvn_factory.addSteps([
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
    steps.SetPropertyFromCommand(
        name="Add configuration to flags",
        command=["echo", util.Interpolate("%(prop:flags)s LLVM_VER=svn")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    steps.ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s cleanall")]
    ),
    steps.ShellCommand(
    	name="make distclean-llvm",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s -C deps distclean-llvm")]
    ),

    # Make!
    steps.ShellCommand(
    	name="make",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s")],
    	haltOnFailure = True
    ),

    # Print versioninfo. This is particularly useful for llvm-svn build
    # since it includes the llvm version number.
    steps.ShellCommand(
    	name="versioninfo()",
    	command=["usr/bin/julia", "-f", "-e", "versioninfo()"]
    ),
    # Test!
    steps.ShellCommand(
    	name="make testall",
    	command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s testall")]
    )
])

for arch in ["x86", "x64"]:
    c['builders'].append(util.BuilderConfig(
        name="nightly_llvmsvn-%s"%(arch),
        workernames=["ubuntu16_04-%s"%(arch)],
        tags=["Nightlies"],
        factory=julia_llvmsvn_factory
    ))
