###############################################################################
# Define everything needed to create source balls for Launchpad Julia binaries
###############################################################################

# Add a dependent scheduler for launchpad upload
launchpad_package_scheduler = Dependent(name="Julia launchpad package", builderNames=["package_launchpad"], upstream=quickbuild_scheduler)
c['schedulers'].append(launchpad_package_scheduler)

# Steps to build the source balls for Launchpad
launchpad_package_factory = BuildFactory()
launchpad_package_factory.useProgress = True
launchpad_package_factory.addSteps([
    # Be a wimp and just use a bash script
    MasterShellCommand(
    	name="Run launchpad.sh",
    	command=["../commands/launchpad.sh", Interpolate("%(prop:revision)s")]
    ),
    SetPropertyFromCommand(
    	name="Get shortcommit",
    	command=["/bin/bash", "-c", Interpolate("echo %(prop:revision)s | cut -c1-10")],
    	property="shortcommit"
    ),
    MasterShellCommand(
    	name="Report success",
    	command=["curl", "-L", "-H", "Content-type: application/json", "-d", Interpolate('{"target": "Launchpad", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"]
    )
])

# Add launchpad julia packager
c['builders'].append(BuilderConfig(
    name="package_launchpad",
    slavenames=ubuntu_names,
    category="Packaging",
    factory=launchpad_package_factory
))
