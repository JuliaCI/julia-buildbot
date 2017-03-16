###############################################################################
# Define everything needed to create source balls for Launchpad Julia binaries
###############################################################################

# Add a dependent scheduler for launchpad upload
launchpad_package_scheduler = schedulers.Dependent(name="Julia launchpad package", builderNames=["package_launchpad"], upstream=packager_scheduler)
c['schedulers'].append(launchpad_package_scheduler)

# Steps to build the source balls for Launchpad
launchpad_package_factory = util.BuildFactory()
launchpad_package_factory.useProgress = True
launchpad_package_factory.addSteps([
    # Be a wimp and just use a bash script
    steps.MasterShellCommand(
    	name="Run launchpad.sh",
    	command=["../commands/launchpad.sh", util.Interpolate("%(prop:revision)s")]
    ),
    steps.SetPropertyFromCommand(
    	name="Get shortcommit",
    	command=["/bin/bash", "-c", util.Interpolate("echo %(prop:revision)s | cut -c1-10")],
    	property="shortcommit"
    ),
    steps.MasterShellCommand(
    	name="Report success",
        command=["/bin/bash", "-c", util.Interpolate("~/bin/try_thrice curl -L -H 'Content-type: application/json' -d '{\"target\": \"Launchpad\", \"version\": \"%(prop:shortcommit)s\"}' https://status.julialang.org/put/nightly")],
    )
])

# Add a manual scheduler for running code snippet
launchpad_force_scheduler = schedulers.ForceScheduler(
    name="force_launchpad",
    label="Run a launchpad packaging",
    builderNames=["package_launchpad"],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default="HEAD"),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Julia"),
        )
    ],
    properties=[
    ]
)
c['schedulers'].append(launchpad_scheduler)


# Add launchpad julia packager
c['builders'].append(util.BuilderConfig(
    name="package_launchpad",
    workernames=ubuntu_names,
    tags=["Packaging"],
    factory=launchpad_package_factory
))
