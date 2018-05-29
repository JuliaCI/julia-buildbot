###############################################################################
# Define everything needed to clean deps and nuke julia checkouts completely
###############################################################################

# Add a manual scheduler for clearing out package_ and build_ arpack, openblas, suite-sparse deps
nuclear_arsenal = {
    "nuke": {
        "label": "Nuke all build/package directories",
        "command": [
            "/bin/sh",
            "-c",
            "if [ `uname` = Darwin ]; \
                then sudo rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; \
            else \
                rm -rf ../../{package_,build_,coverage_,juno_,nightly_,perf_}*; \
            fi",
        ],
    },
}

for name in nuclear_arsenal:
    scheduler = schedulers.ForceScheduler(
        name = name,
        label = nuclear_arsenal[name]["label"],
        builderNames = [name + "_" + builder for builder in builder_mapping],
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
        properties =[]
    )
    c['schedulers'].append(scheduler)

    factory = util.BuildFactory()
    factory.useProgress = True
    factory.addSteps([
        steps.ShellCommand(
            name=nuclear_arsenal[name]["label"],
            command=nuclear_arsenal[name]["command"],
        ),
    ])

    for builder, worker in builder_mapping.iteritems():
        c['builders'].append(util.BuilderConfig(
            name=name + "_" + builder,
            workernames=[worker],
            tags=["Cleaning"],
            factory=factory
        ))
