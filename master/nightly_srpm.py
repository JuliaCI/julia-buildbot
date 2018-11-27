###############################################################################
# Define everything needed to create SRPMs for copr (Fedora build farm)
###############################################################################

julia_srpm_package_factory = util.BuildFactory()
julia_srpm_package_factory.useProgress = True
julia_srpm_package_factory.addSteps([
    # Clone julia, clear out temporary files from last time...
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
    steps.ShellCommand(
        name="Cleanup build artifacts",
        command=["rm", "-rf", "../SOURCES", "../SPECS", "../SRPMS", "../BUILD", "../BUILDROOT", "../RPMS"]
    ),

    # Bake in version_git.jl.phony
    steps.ShellCommand(
        name="Bake in versioning info",
        command=[util.Interpolate("%(prop:make_cmd)s"), "-C", "base", "version_git.jl.phony"]
    ),

    # Get Julia version, commit and date of commit
    steps.SetPropertyFromCommand(
        name="Get Julia version",
        command=["/bin/sh", "-c", "echo $(cat ./VERSION | cut -f1 -d'-')"],
        property="juliaversion"
    ),
    steps.SetPropertyFromCommand(
        name="Get full Julia version",
        command=["/bin/sh", "-c", "echo $(cat ./VERSION)"],
        property="juliafullversion"
    ),
    steps.SetPropertyFromCommand(
        name="Get commit",
        command=["/bin/sh", "-c", "echo $(git rev-parse --short=10 HEAD)"],
        property="juliacommit"
    ),
    steps.SetPropertyFromCommand(
        name="Get date of commit",
        command=["/bin/sh", "-c", "echo $(git log --pretty=format:'%cd' --date=short -n 1 | tr -d '-')"],
        property="datecommit"
    ),
    steps.SetPropertyFromCommand(
        name="Get libuv commit",
        command=["/bin/sh", "-c", "cat deps/libuv.version | cut -f2 -d'=' | tail -n 1"],
        property="libuvcommit"
    ),

    # Build tarballs for Julia and all dependencies
    steps.ShellCommand(
        name="mkdir SOURCES",
        command=["mkdir", "-p", "../SOURCES"]
    ),
    steps.FileDownload(
        mastersrc="../commands/julia_juliadoc.patch",
        workerdest="../SOURCES/julia_juliadoc.patch"
    ),
    steps.ShellCommand(
        name="Tarballify julia",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s light-source-dist && tar xzf julia-%(prop:juliafullversion)s_%(prop:juliacommit)s.tar.gz && mv $(basename $(pwd)) julia && tar czf ../SOURCES/julia.tar.gz julia && rm -R julia/ julia-%(prop:juliafullversion)s_%(prop:juliacommit)s.tar.gz")]
    ),

    # Prepare .spec file
    steps.ShellCommand(
        name="mkdir SPECS",
        command=["mkdir", "-p", "../SPECS"]
    ),
    steps.FileDownload(
        mastersrc="../commands/julia-nightlies.spec",
        workerdest="../SPECS/julia-nightlies.spec"
    ),
    steps.ShellCommand(
        name="replace datecommit and juliaversion in .spec",
        command=["/bin/sh", "-c", util.Interpolate("sed -i -e 's/%%{datecommit}/%(prop:datecommit)s/g' -e 's/%%{juliaversion}/%(prop:juliaversion)s/g' -e 's/%%{uvcommit}/%(prop:libuvcommit)s/g' ../SPECS/julia-nightlies.spec")]
    ),

    # Download non-submodule dependencies (currently Rmath-julia and libuv)
    steps.ShellCommand(
        name="Download missing tarballs",
        command=["/bin/sh", "-c", "cd ../SOURCES && spectool -g ../SPECS/julia-nightlies.spec"]
    ),

    # Build SRPM
    steps.ShellCommand(
        name="Build SRPM",
        command=["/bin/sh", "-c", "rpmbuild -bs SPECS/julia-nightlies.spec --define '_topdir .' --define '_source_filedigest_algorithm md5' --define '_binary_filedigest_algorithm md5'"],
        workdir=".",
        haltOnFailure = True
    ),

    # Upload SRPM to master, which in turn uploads it to AWS
    steps.SetPropertyFromCommand(
        name="Get SRPM filename",
        command=["/bin/sh", "-c", "echo *.rpm"],
        workdir="SRPMS",
        property="filename"
    ),
    steps.FileUpload(
        workersrc=util.Interpolate("../SRPMS/%(prop:filename)s"),
        masterdest=util.Interpolate("/tmp/julia_package/%(prop:filename)s"),
        haltOnFailure = True
    ),
    steps.MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/sh", "-c", util.Interpolate("aws s3 cp --acl public-read /tmp/julia_package/%(prop:filename)s s3://julialangnightlies/bin/srpm/%(prop:filename)s ")],
        haltOnFailure=True
    ),

    # Tell copr where to build from
    steps.ShellCommand(
        name="Bully Copr into building for us",
        command=["copr-cli", "build", "nalimilan/julia-nightlies", util.Interpolate("https://s3.amazonaws.com/julialangnightlies/bin/srpm/%(prop:filename)s")],
        timeout=3600,
        flunkOnFailure=False
    ),

    # Report back to the mothership
    steps.SetPropertyFromCommand(
        name="Get shortcommit",
        command=["/bin/sh", "-c", util.Interpolate("echo %(prop:revision)s | cut -c1-10")],
        property="shortcommit"
    ),
    steps.MasterShellCommand(
        name="Report success",
        command=["/bin/sh", "-c", util.Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"Copr\", \"url\": \"https://s3.amazonaws.com/julialangnightlies/buildog/bin/srpm/%(prop:filename)s\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
    )
])

# Add a dependent scheduler for SRPM packaging
julia_srpm_builders = ["nightly_srpm"]
srpm_package_scheduler = schedulers.Nightly(
    name="Julia SRPM package",
    builderNames=julia_srpm_builders,
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia','staticfloat/julia'],
        branch='master'
    ),
    hour=[0],
    onlyIfChanged=True
)
c['schedulers'].append(srpm_package_scheduler)



# Add SRPM packager
c['builders'].append(util.BuilderConfig(
    name="nightly_srpm",
    workernames=builder_mapping["linux64"],
    tags=["Nightlies"],
    factory=julia_srpm_package_factory,
))
