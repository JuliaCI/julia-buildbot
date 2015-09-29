###############################################################################
# Define everything needed to build Ubuntu .deb packages without Launchpad
###############################################################################

julia_ubuntu_packagers = ["package_" + z for z in ubuntu_names]
ubuntu_package_scheduler = Dependent(name="Julia ubuntu package", builderNames=julia_ubuntu_packagers, upstream=quickbuild_scheduler)
c['schedulers'].append(ubuntu_package_scheduler)


# Steps to build an Ubuntu .deb Julia Package
ubuntu_package_julia_factory = BuildFactory()
ubuntu_package_julia_factory.useProgress = True
ubuntu_package_julia_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present) so sha's
    # that haven't been seen before don't cause rebuilds from scratch
    ShellCommand(
        name="git fetch",
        command=["git", "fetch"],
        flunkOnFailure=False
    ),

    # Clone julia
    Git(name="Julia checkout", repourl=Property('repository', default='git://github.com/JuliaLang/julia.git'), mode='incremental', method='clean', submodules=True, clobberOnFailure=True, progress=True),

    # Perform pre-tarball steps
    ShellCommand(name="version_git.jl", command=["make", "-C", "base", "version_git.jl.phony"]),
    ShellCommand(name="Get dependencies", command=["make", "-C", "deps", "get-dsfmt", "get-virtualenv", "get-libgit2"]),

    # Save the combined version string and release
    SetPropertyFromCommand(name="Compute debversion", command=["/bin/bash", "-c", "echo $(cat ./VERSION | cut -f1 -d'-')~pre+$(git rev-list HEAD ^$(git describe --tags --abbrev=0) | wc -l | sed -e 's/[^[:digit:]]//g')"], property="debversion"),

    # Make the source tarball
    ShellCommand(name="Source Tarball", command=["/bin/bash", "-c", Interpolate("tar --exclude .git -czf ../julia_%(prop:debversion)s.orig.tar.gz .")]),

    # Get the debian/ directory
    ShellCommand(name="Get debian/", command=["/bin/bash", "-c", "rm -rf debian; wget https://github.com/staticfloat/julia-debian/archive/master.tar.gz -O- | tar -zx --exclude README.md --strip-components=1"]),
    
    # Bump the version
    ShellCommand(name="Bump debian version", command=["/bin/bash", "-c", Interpolate("EMAIL='Elliot Saba <staticfloat@gmail.com>' dch -v %(prop:debversion)s 'nightly git build'")]),
    # Build the .deb!
    ShellCommand(name="debuild", command=["debuild"]),
    
    # Upload the result!
    MasterShellCommand(name="mkdir julia_package", command=["mkdir", "-p", "/tmp/julia_package"]),
    FileUpload(slavesrc=Interpolate("../julia_%(prop:debversion)s_%(prop:deb_arch)s.deb"), masterdest=Interpolate("/tmp/julia_package/julia_%(prop:debversion)s~%(prop:release)s_%(prop:deb_arch)s.deb")),

    # Since this stuff is getting thrown into the parent directory, we need to clean up after ourselves!
    ShellCommand(name="cleanup", command=["/bin/bash", "-c", "rm -f ../*.{gz,build,dsc,deb,changes}"]),

    # Upload it to AWS and cleanup the master!
    MasterShellCommand(name="Upload to AWS", command=["/bin/bash", "-c", Interpolate("~/bin/aws put --fail --public julianightlies/bin/ubuntu/julia_%(prop:debversion)s~%(prop:release)s_%(prop:deb_arch)s.deb /tmp/julia_package/julia_%(prop:debversion)s~%(prop:release)s_%(prop:deb_arch)s.deb")], haltOnFailure=True),
    MasterShellCommand(name="Cleanup Master", command=["rm", "-f", Interpolate("/tmp/julia_package/julia_%(prop:debversion)s~%(prop:release)s_%(prop:deb_arch)s.deb")])
])





# Add all the ubuntu julia packagers
for name in ubuntu_names:
   c['builders'].append(BuilderConfig(
       name="package_%s"%(name),
       slavenames=[name],
       category="Packaging",
       factory=ubuntu_package_julia_factory
   ))
