###############################################################################
# Define everything needed to create .exe files for Windows Julia binaries
###############################################################################

# Add a dependent scheduler for Windows packaging
julia_win_packagers = ["package_" + z for z in win_names]
win_package_scheduler = Dependent(name="Julia Windows package", builderNames=julia_win_packagers, upstream=quickbuild_scheduler)
c['schedulers'].append(win_package_scheduler)

# Steps to build a windows .exe Julia package
win_package_factory = BuildFactory()
win_package_factory.useProgress = True
win_package_factory.addSteps([
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
        name="make",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s")],
        haltOnFailure = True
    ),
    ShellCommand(
        name="make win-extras",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s win-extras")],
        haltOnFailure = True
    ),
    ShellCommand(
        name="make binary-dist",
        command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s binary-dist")],
        haltOnFailure = True
    ),

    # Set a bunch of properties that everyone will need
    SetPropertyFromCommand(
        name="Get major/minor version",
        command=["usr/bin/julia.exe", "-e", "println(\"$(VERSION.major).$(VERSION.minor)\")"],
        property="majmin"
    ),
    SetPropertyFromCommand(
        name="Get major/minor/patch version",
        command=["usr/bin/julia.exe", "-e", "println(\"$(VERSION.major).$(VERSION.minor).$(VERSION.patch)\")"],
        property="version"
    ),
    SetPropertyFromCommand(
        name="Get shortcommit",
        command=["usr/bin/julia.exe", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
        property="shortcommit"
    ),

    # Upload the result (after we sign it)
    MasterShellCommand(
        name="mkdir julia_package",
        command=["mkdir", "-p", "/tmp/julia_package"]
    ),
    SetPropertyFromCommand(
        name="Get exe filename",
        command=["/bin/bash", "-c", "echo julia-*.exe"],
        property="filename"
    ),
    ShellCommand(
        name="Sign exe",
        command=["/bin/bash", "-c", Interpolate("~/sign.sh %(prop:filename)s")]
    ),

    FileUpload(
        slavesrc=Interpolate("%(prop:filename)s"),
        masterdest=Interpolate("/tmp/julia_package/%(prop:filename)s")
    ),

    # Upload it to AWS and cleanup the master!
    MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/winnt/%(prop:up_arch)s/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-win%(prop:bits)s.exe /tmp/julia_package/%(prop:filename)s")],
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/winnt/%(prop:up_arch)s/julia-latest-win%(prop:bits)s.exe /tmp/julia_package/%(prop:filename)s")],
        doStepIf=is_nightly_build,
        haltOnFailure=True
    ),
    MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", Interpolate("/tmp/julia_package/julia-%(prop:shortcommit)s-Linux-%(prop:tar_arch)s.tar.gz")]
    ),

    # Stupid windows HTTPS problems
    MasterShellCommand(
        name="Report success",
        command=["curl", "-L", "-H", "Content-type: application/json", "-d", Interpolate('{"target": "win%(prop:bits)s", "url":"https://s3.amazonaws.com/julianightlies/bin/winnt/%(prop:up_arch)s/%(prop:majmin)s/julia-%(prop:version)s-%(prop:shortcommit)s-win%(prop:bits)s.exe", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"],
        doStepIf=is_nightly_build
    )
])

# Add the windows julia packagers
for name in win_names:
    c['builders'].append(BuilderConfig(
        name="package_%s"%(name),
        slavenames=[name],
        category="Packaging",
        factory=win_package_factory
    ))
