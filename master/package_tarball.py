###############################################################################
# Define everything needed to create .tar.gz files for Linux Julia binaries
###############################################################################

# Add a dependent scheduler for generic linux tarball builds
julia_tarball_packagers = ["package_tarball32", "package_tarball64"]
tarball_package_scheduler = Dependent(name="Julia Tarball package", builderNames=julia_tarball_packagers, upstream=quickbuild_scheduler)
c['schedulers'].append(tarball_package_scheduler)

# Steps to build a `make binary-dist` tarball that should work on just about every linux ever
julia_tarball_factory = BuildFactory()
julia_tarball_factory.useProgress = True
julia_tarball_factory.addSteps([
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

    # make clean first
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
    SetPropertyFromCommand(
        name="Get commitmessage",
        command=["git", "log", "-1", "--pretty=format:%s"],
        property="commitmessage"
    ),
    SetPropertyFromCommand(
        name="Get commitname",
        command=["git", "log", "-1", "--pretty=format:%cN"],
        property="commitname"
    ),
    SetPropertyFromCommand(
        name="Get commitemail",
        command=["git", "log", "-1", "--pretty=format:%cE"],
        property="commitemail"
    ),
    SetPropertyFromCommand(
        name="Get authorname",
        command=["git", "log", "-1", "--pretty=format:%aN"],
        property="authorname"
    ),
    SetPropertyFromCommand(
        name="Get authoremail",
        command=["git", "log", "-1", "--pretty=format:%aE"],
        property="authoremail"
    ),
    
    # Upload the result!
    MasterShellCommand(
    	name="mkdir julia_package",
    	command=["mkdir", "-p", "/tmp/julia_package"]
    ),
    FileUpload(
    	slavesrc=Interpolate("julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz"),
    	masterdest=Interpolate("/tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")
    ),

    # Upload it to AWS and cleanup the master!
    MasterShellCommand(
    	name="Upload to AWS",
    	command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz /tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
    	haltOnFailure=True
    ),
    MasterShellCommand(
    	name="Upload to AWS (latest)",
    	command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/linux/%(prop:up_arch)s/julia-latest-linux%(prop:bits)s.tar.gz /tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")],
    	doStepIf=is_nightly_build,
    	haltOnFailure=True
    ),
    MasterShellCommand(
    	name="Cleanup Master",
    	command=["rm", "-f", Interpolate("/tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),

    ShellCommand(
    	name="Report success",
    	command=["curl", "-L", "-H", "Content-type: application/json", "-d", Interpolate('{"target": "linux-%(prop:tar_arch)s", "url":"https://s3.amazonaws.com/julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"],
    	doStepIf=is_nightly_build
    ),

    # Trigger a download of this file onto another slave for coverage purposes
    Trigger(schedulerNames=["Julia Coverage Testing"],
        set_properties={
            'url': Interpolate('https://s3.amazonaws.com/julianightlies/bin/linux/%(prop:up_arch)s/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-linux%(prop:bits)s.tar.gz'),
            'commitmessage': Property('commitmessage'),
            'commitname': Property('commitname'),
            'commitemail': Property('commitemail'),
            'authorname': Property('authorname'),
            'authoremail': Property('authoremail'),
            'shortcommit': Property('shortcommit'),
        },
        waitForFinish=False,
        doStepIf=should_run_coverage
    )
])


# Add linux tarball builders
c['builders'].append(BuilderConfig(
    name="package_tarball32",
    slavenames=["centos5.11-x86"],
    category="Packaging",
    factory=julia_tarball_factory
))

c['builders'].append(BuilderConfig(
    name="package_tarball64",
    slavenames=["centos5.11-x64"],
    category="Packaging",
    factory=julia_tarball_factory
))
