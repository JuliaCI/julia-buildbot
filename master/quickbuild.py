###############################################################################
# Define everything needed for the quickbuild jobs that build and test a commit
###############################################################################

# Add a scheduler for julia continuous integration (Omit windows for now)
julia_quickbuilders = ["build_" + z for z in ubuntu_names + ["centos7.1-x64"] + ["osx10.9-x64"]]
quickbuild_scheduler = AnyBranchScheduler(name="julia quickbuild", treeStableTimer=1, builderNames=julia_quickbuilders)
c['schedulers'].append(quickbuild_scheduler)

# Add a manual scheduler for running forced builds
c['schedulers'].append(ForceScheduler(
    name="Build and test",
    builderNames=julia_quickbuilders,
    reason=FixedParameter(name="reason", default=""),
    branch=StringParameter(name="branch", label="Branch", size=30, default="master"),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Packaging"),
    properties=[
    ]
))


# Steps to do a quickbuild of julia
quickbuild_factory = BuildFactory()
quickbuild_factory.useProgress = True
quickbuild_factory.addSteps([
    # Clone julia
    Git(name="Julia checkout", repourl=Property('repository', default='git://github.com/JuliaLang/julia.git'), mode='incremental', method='clean', submodules=True, clobberOnFailure=True, progress=True),

    # make clean first
    ShellCommand(command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s cleanall")]),

    # Make!
    ShellCommand(command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s")], haltOnFailure = True, timeout=3600),

    # Test!
    ShellCommand(command=["/bin/bash", "-c", Interpolate("make %(prop:flags)s testall")], timeout=3600)
])

# Add builders that link to the factory above
for name in ubuntu_names + ["osx10.9-x64"] + ["centos7.1-x64"]:
    c['builders'].append(BuilderConfig(
        name="build_%s"%(name),
        slavenames=[name],
        category="Quickbuild",
        factory=quickbuild_factory
    ))
