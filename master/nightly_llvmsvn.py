###############################################################################
# Define everything needed to build nightly Julia builds against LLVM SVN
###############################################################################

llvmsvn_nightly_scheduler = Nightly(name="Julia LLVM SVN Build", builderNames=["build_llvmsvn_nightly-x86", "build_llvmsvn_nightly-x64"], hour=[0,8,16], branch="master", onlyIfChanged=True)
c['schedulers'].append(llvmsvn_nightly_scheduler)

llvmsvn_build_factory = BuildFactory()
llvmsvn_build_factory.useProgress = True
llvmsvn_build_factory.addSteps([
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

    # make clean first, and nuke llvm
    ShellCommand(
    	name="make cleanall",
    	command=["make", "LLVM_VER=svn", "VERBOSE=1", "cleanall"]
    ),
    ShellCommand(
    	name="make distclean-llvm",
    	command=["make", "LLVM_VER=svn", "VERBOSE=1", "-C", "deps", "distclean-llvm"]
    ),

    # Make!
    ShellCommand(
    	name="make",
    	command=["make", "LLVM_VER=svn", "VERBOSE=1"],
    	haltOnFailure = True
    ),

    # Test!
    ShellCommand(
    	name="make testall",
    	command=["make", "LLVM_VER=svn", "VERBOSE=1", "testall"]
    )
])

for arch in ["x86", "x64"]:
    c['builders'].append(BuilderConfig(
        name="build_llvmsvn_nightly-%s"%(arch),
        slavenames=["ubuntu14.04-%s"%(arch)],
        category="Nightlies",
        factory=llvmsvn_build_factory
    ))
