###############################################################################
# Define everything needed to clean deps and nuke julia checkouts completely
###############################################################################

# Add a manual scheduler for clearing out package_ and build_ arpack, openblas, suite-sparse deps
clean_names = ubuntu_names + ["osx10_10-x64"] + centos_names + debian_names + win_names
clean_scheduler = schedulers.ForceScheduler(
    name="clean",
    label="clean arpack, openblas, suite-sparse, openlibm and openspecfun",
    builderNames=["clean_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Cleaning"),
        )
    ],
    properties =[
    ]
)
c['schedulers'].append(clean_scheduler)

# Add a manual scheduler for clearing out package_ and build_ mbedtls, libssh2, curl, libgit2 deps
cleanpkg_scheduler = schedulers.ForceScheduler(
    name="cleanpkg",
    label="clean mbedtls, libssh2, curl, and libgit2",
    builderNames=["cleanpkg_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Cleaning"),
        )
    ],
    properties =[
    ]
)
c['schedulers'].append(cleanpkg_scheduler)

# Add a manual scheduler for clearing out EVERYTHING
nuclear_scheduler = schedulers.ForceScheduler(
    name="nuke",
    label="Nuke all build/package directories",
    builderNames=["nuke_" + x for x in clean_names],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Cleaning"),
        )
    ],
    properties =[
    ]
)
c['schedulers'].append(nuclear_scheduler)

clean_factory = util.BuildFactory()
clean_factory.useProgress = True
clean_factory.addSteps([
    steps.ShellCommand(
    	name="clean deps",
    	command=["/bin/bash", "-c", "for f in ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; do ([[ -d $f/build/deps ]] && cd $f/build/deps && make distclean-arpack distclean-suitesparse distclean-openblas distclean-openlibm distclean-openspecfun); done; echo Done"]
    )
])

cleanpkg_factory = util.BuildFactory()
cleanpkg_factory.useProgress = True
cleanpkg_factory.addSteps([
    steps.ShellCommand(
    	name="clean pkg deps",
    	command=["/bin/bash", "-c", "for f in ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; do ([[ -d $f/build/deps ]] && cd $f/build/deps && make distclean-mbedtls distclean-libssh2 distclean-curl distclean-libgit2); done; echo Done"]
    )
])

nuclear_factory = util.BuildFactory()
nuclear_factory.useProgress = True
nuclear_factory.addSteps([
    steps.ShellCommand(
    	name="Do your thing, Duke",
    	command=["/bin/bash", "-c", "if [ `uname` = Darwin ]; then sudo rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; else rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; fi"]
    )
])

# Add deps cleaners
for name in clean_names:
    c['builders'].append(util.BuilderConfig(
        name="clean_%s"%(name),
        workernames=[name],
        tags=["Cleaning"],
        factory=clean_factory,
    ))

# Add pkg deps cleaners
for name in clean_names:
    c['builders'].append(util.BuilderConfig(
        name="cleanpkg_%s"%(name),
        workernames=[name],
        tags=["Cleaning"],
        factory=cleanpkg_factory,
    ))

# Add nuclear cleaners
for name in clean_names:
    c['builders'].append(util.BuilderConfig(
        name="nuke_%s"%(name),
        workernames=[name],
        tags=["Cleaning"],
        factory=nuclear_factory,
    ))
