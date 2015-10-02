###############################################################################
# Define everything needed to create .dmg files for OSX Julia binaries
###############################################################################

# Add a dependent scheduler for OSX packaging
julia_dmg_packagers = ["package_" + z for z in ["osx10.9-x64"]]
osx_package_scheduler = Dependent(name="Julia OSX package", builderNames=julia_dmg_packagers, upstream=quickbuild_scheduler)
c['schedulers'].append(osx_package_scheduler)

# Steps to build an OSX .dmg Julia package
julia_dmg_factory = BuildFactory()
julia_dmg_factory.useProgress = True
julia_dmg_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present) so sha's
    # that haven't been seen before don't cause rebuilds from scratch
    ShellCommand(
    	name="git fetch",
    	command=["git", "fetch"],
    	flunkOnFailure=False
    ),

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

    # Unlink brew dependencies
    ShellCommand(
    	name="Unlink brew dependencies",
    	command=["brew", "unlink", "llvm33-julia", "arpack-julia", "suite-sparse-julia", "openblas-julia"],
    	flunkOnFailure=False
    ),
    # Make sure gcc and cmake are installed though!
    ShellCommand(
    	name="Install necessary brew dependencies",
    	command=["brew", "install", "gcc", "cmake"],
        flunkOnFailure=False
    ),

    # make clean first
    ShellCommand(
    	name="make cleanall",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]
    ),

    # Make!
    ShellCommand(
    	name="make",
    	command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s")],
    	haltOnFailure=True
    ),

    # Set a bunch of properties that everyone will need
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

    # Actually package the darn thing
    ShellCommand(
    	name="make .app",
    	command=["/bin/bash", "-c", Interpolate("~/unlock_keychain.sh && make %(prop:flags)s -C contrib/mac/app")],
    	haltOnFailure=True
    ),

    # Upload the package to the host!
    SetPropertyFromCommand(
    	name="Get dmg filename",
    	command=["/bin/bash", "-c", "cd contrib/mac/app && echo *.dmg"],
    	property="filename"
    ),
    MasterShellCommand(
    	name="mkdir julia_package",
    	command=["mkdir", "-p", "/tmp/julia_package"]
    ),
    FileUpload(
    	slavesrc=Interpolate("contrib/mac/app/%(prop:filename)s"),
    	masterdest=Interpolate("/tmp/julia_package/%(prop:filename)s")
    ),
    MasterShellCommand(
    	name="Upload to AWS",
    	command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/osx/x64/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-osx.dmg /tmp/julia_package/%(prop:filename)s")],
    	haltOnFailure=True
    ),
    MasterShellCommand(
    	name="Upload to AWS (latest)",
    	command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julianightlies/bin/osx/x64/julia-latest-osx.dmg /tmp/julia_package/%(prop:filename)s")],
    	doStepIf=is_nightly_build,
    	haltOnFailure=True
    ),
    MasterShellCommand(
    	name="Cleanup Master",
    	command=["rm", "-f", Interpolate("/tmp/julia_package/%(prop:filename)s")]
    ),

    # Cleanup the slave
    ShellCommand(
    	command=["make", "-C", "contrib/mac/app", "clean"],
    	haltOnFailure=True
    ),

    # Report back to the mothership
    MasterShellCommand(
    	name="Report success",
    	command=["/bin/bash", "-c", Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"osx10.7+\", \"url\": \"https://s3.amazonaws.com/julianightlies/bin/osx/x64/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-osx.dmg\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
    	doStepIf=is_nightly_build
    ),
])


# Add my osx julia packager (we only need one!)
c['builders'].append(BuilderConfig(
    name="package_%s"%("osx10.9-x64"),
    slavenames=["osx10.9-x64"],
    category="Packaging",
    factory=julia_dmg_factory,
))
