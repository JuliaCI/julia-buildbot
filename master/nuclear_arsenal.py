###############################################################################
# Define everything needed to clean deps and nuke julia checkouts completely
###############################################################################

# Add a manual scheduler for clearing out package_ and build_ arpack, openblas, suite-sparse deps
clean_names = ubuntu_names + ["osx10.9-x64"] + centos_names + win_names
clean_scheduler = schedulers.ForceScheduler(
    name="clean arpack, openblas, suite-sparse, openlibm and openspecfun",
    builderNames=["clean_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    branch=util.FixedParameter(name="branch", default=""),
    revision=util.FixedParameter(name="revision", default=""),
    repository=util.FixedParameter(name="repository", default=""),
    project=util.FixedParameter(name="project", default="Cleaning"),
    properties =[
    ]
)
c['schedulers'].append(clean_scheduler)

# Add a manual scheduler for clearing out package_ and build_ mbedtls, libssh2, curl, libgit2 deps
cleanpkg_scheduler = schedulers.ForceScheduler(
    name="clean mbedtls, libssh2, curl, and libgit2",
    builderNames=["cleanpkg_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    branch=util.FixedParameter(name="branch", default=""),
    revision=util.FixedParameter(name="revision", default=""),
    repository=util.FixedParameter(name="repository", default=""),
    project=util.FixedParameter(name="project", default="Cleaning"),
    properties =[
    ]
)
c['schedulers'].append(cleanpkg_scheduler)

# Add a manual scheduler for clearing out EVERYTHING
nuclear_scheduler = schedulers.ForceScheduler(
    name="Nuke all build/package directories",
    builderNames=["nuke_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    branch=util.FixedParameter(name="branch", default=""),
    revision=util.FixedParameter(name="revision", default=""),
    repository=util.FixedParameter(name="repository", default=""),
    project=util.FixedParameter(name="project", default="Cleaning"),
    properties =[
    ]
)
c['schedulers'].append(nuclear_scheduler)

clean_factory = BuildFactory()
clean_factory.useProgress = True
clean_factory.addSteps([
    ShellCommand(
    	name="clean deps",
    	command=["/bin/bash", "-c", "for f in ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; do ([[ -d $f/build/deps ]] && cd $f/build/deps && make distclean-arpack distclean-suitesparse distclean-openblas distclean-openlibm distclean-openspecfun); done; echo Done"]
    )
])

cleanpkg_factory = BuildFactory()
cleanpkg_factory.useProgress = True
cleanpkg_factory.addSteps([
    ShellCommand(
    	name="clean pkg deps",
    	command=["/bin/bash", "-c", "for f in ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; do ([[ -d $f/build/deps ]] && cd $f/build/deps && make distclean-mbedtls distclean-libssh2 distclean-curl distclean-libgit2); done; echo Done"]
    )
])

nuclear_factory = BuildFactory()
nuclear_factory.useProgress = True
nuclear_factory.addSteps([
    ShellCommand(
    	name="Do your thing, Duke",
    	command=["/bin/bash", "-c", "if [ `uname` = Darwin ]; then sudo rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; else rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; fi"]
    )
])

# Add deps cleaners
for name in clean_names:
    c['builders'].append(BuilderConfig(
        name="clean_%s"%(name),
        slavenames=[name],
        category="Cleaning",
        factory=clean_factory,
    ))

# Add pkg deps cleaners
for name in clean_names:
    c['builders'].append(BuilderConfig(
        name="cleanpkg_%s"%(name),
        slavenames=[name],
        category="Cleaning",
        factory=cleanpkg_factory,
    ))

# Add nuclear cleaners
for name in clean_names:
    c['builders'].append(BuilderConfig(
        name="nuke_%s"%(name),
        slavenames=[name],
        category="Cleaning",
        factory=nuclear_factory,
    ))
