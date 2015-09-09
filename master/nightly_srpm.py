###############################################################################
# Define everything needed to create SRPMs for copr (Fedora build farm)
###############################################################################

# Add a dependent scheduler for SRPM packaging
julia_srpm_builders  = ["nightly_srpm"]
srpm_package_scheduler = Nightly(name="Julia SRPM package", builderNames=julia_srpm_builders, branch="master", hour=[0], onlyIfChanged=True)
c['schedulers'].append(srpm_package_scheduler)

julia_srpm_package_factory = BuildFactory()
julia_srpm_package_factory.useProgress = True
julia_srpm_package_factory.addSteps([
    # Clone julia, clear out temporary files from last time...
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
    ShellCommand(
    	name="Cleanup build artifacts",
    	command=["rm", "-rf", "../SOURCES", "../SPECS", "../SRPMS", "../BUILD", "../BUILDROOT", "../RPMS"]
    ),

    # Bake in version_git.jl.phony
    ShellCommand(
    	name="Bake in versioning info",
    	command=["make", "-C", "base", "version_git.jl.phony"]
    ),

    # Get Julia version, commit and date of commit
    SetPropertyFromCommand(
    	name="Get Julia version",
    	command=["/bin/bash", "-c", "echo $(cat ./VERSION | cut -f1 -d'-')"],
    	property="juliaversion"
    ),
    SetPropertyFromCommand(
        name="Get full Julia version",
        command=["/bin/bash", "-c", "echo $(cat ./VERSION)"],
        property="juliafullversion"
    ),
    SetPropertyFromCommand(
        name="Get commit",
        command=["/bin/bash", "-c", "echo $(git rev-parse --short=10 HEAD)"],
        property="juliacommit"
    ),
    SetPropertyFromCommand(
    	name="Get date of commit",
    	command=["/bin/bash", "-c", "echo $(git log --pretty=format:'%cd' --date=short -n 1 | tr -d '-')"],
    	property="datecommit"
    ),
    SetPropertyFromCommand(
        name="Get libuv commit",
        command=["/bin/bash", "-c", "cat deps/libuv.version | cut -f2 -d'=' | tail -n 1"],
        property="libuvcommit"
    ),

    # Build tarballs for Julia and all dependencies
    ShellCommand(
    	name="mkdir SOURCES",
    	command=["mkdir", "-p", "../SOURCES"]
    ),
    FileDownload(
        mastersrc="../commands/julia_juliadoc.patch",
        slavedest="../SOURCES/julia_juliadoc.patch"
    ),
    ShellCommand(
        name="Tarballify julia",
        command=["/bin/bash", "-c", Interpolate("make light-source-dist && tar xzf julia-%(prop:juliafullversion)s_%(prop:juliacommit)s.tar.gz && mv $(basename $(pwd)) julia && tar czf ../SOURCES/julia.tar.gz julia && rm -R julia/ julia-%(prop:juliafullversion)s_%(prop:juliacommit)s.tar.gz")]
    ),

    # Prepare .spec file
    ShellCommand(
        name="mkdir SPECS",
        command=["mkdir", "-p", "../SPECS"]
    ),
    FileDownload(
        mastersrc="../commands/julia-nightlies.spec",
        slavedest="../SPECS/julia-nightlies.spec"
    ),
    ShellCommand(
        name="replace datecommit and juliaversion in .spec",
        command=["/bin/bash", "-c", Interpolate("sed -i -e 's/%%{datecommit}/%(prop:datecommit)s/g' -e 's/%%{juliaversion}/%(prop:juliaversion)s/g' -e 's/%%{uvcommit}/%(prop:libuvcommit)s/g' ../SPECS/julia-nightlies.spec")]
    ),

    # Download non-submodule dependencies (currently Rmath-julia and libuv)
    ShellCommand(
        name="Download missing tarballs",
        command=["/bin/bash", "-c", "cd ../SOURCES && spectool -g ../SPECS/julia-nightlies.spec"]
    ),

    # Build SRPM
    ShellCommand(
        name="Build SRPM",
        command=["/bin/bash", "-c", "rpmbuild -bs SPECS/julia-nightlies.spec --define '_topdir .' --define '_source_filedigest_algorithm md5' --define '_binary_filedigest_algorithm md5'"],
        workdir=".",
        haltOnFailure = True
    ),

    # Upload SRPM to master, which in turn uploads it to AWS
    SetPropertyFromCommand(
        name="Get SRPM filename",
        command=["/bin/bash", "-c", "echo *.rpm"],
        workdir="SRPMS",
        property="filename"
    ),
    FileUpload(
        slavesrc=Interpolate("../SRPMS/%(prop:filename)s"),
        masterdest=Interpolate("/tmp/julia_package/%(prop:filename)s"),
        haltOnFailure = True
    ),
    MasterShellCommand(
        name="Upload to AWS",
        command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/srpm/%(prop:filename)s /tmp/julia_package/%(prop:filename)s")],
        haltOnFailure=True
    ),

    # Tell copr where to build from
    ShellCommand(
        name="Bully Copr into building for us",
        command=["copr-cli", "build", "nalimilan/julia-nightlies", Interpolate("https://s3.amazonaws.com/julianightlies/bin/srpm/%(prop:filename)s")],
        timeout=3600,
        flunkOnFailure=False
    ),

    # Report back to the mothership
    SetPropertyFromCommand(
        name="Get shortcommit",
        command=["/bin/bash", "-c", Interpolate("echo %(prop:revision)s | cut -c1-10")],
        property="shortcommit"
    ),
    MasterShellCommand(
        name="Report success",
        command=["curl", "-L", "-H", "Content-type: application/json", "-d", Interpolate('{"target": "Copr", "url": "https://s3.amazonaws.com/julianightlies/bin/srpm/%(prop:filename)s", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"]
    )
])


# Add SRPM packager
c['builders'].append(BuilderConfig(
    name="nightly_srpm",
    slavenames=["centos7.1-x64"],
    category="Nightlies",
    factory=julia_srpm_package_factory,
))
