###############################################################################
# Define everything needed to build nightly Julia builds against LLVM SVN
###############################################################################

llvmsvn_nightly_scheduler = Nightly(name="Julia LLVM SVN Build", builderNames=["nightly_llvmsvn-x86", "nightly_llvmsvn-x64"], hour=[0,12], branch="master", onlyIfChanged=True)
c['schedulers'].append(llvmsvn_nightly_scheduler)

julia_llvmsvn_factory = BuildFactory()
julia_llvmsvn_factory.useProgress = True
julia_llvmsvn_factory.addSteps([
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
        command=["echo", Interpolate("%(prop:flags)s LLVM_VER=svn")],
        property="flags"
    ),

    # make clean first, and nuke llvm
    ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]
    ),
    ShellCommand(
    	name="make distclean-llvm",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall -C deps distclean-llvm")]
    ),

    # Make!
    ShellCommand(
    	name="make",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s")],
    	haltOnFailure = True
    ),

    # Test!
    ShellCommand(
    	name="make testall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s testall")]
    )
])

for arch in ["x86", "x64"]:
    c['builders'].append(BuilderConfig(
        name="nightly_llvmsvn-%s"%(arch),
        slavenames=["ubuntu14.04-%s"%(arch)],
        category="Nightlies",
        factory=julia_llvmsvn_factory
    ))
