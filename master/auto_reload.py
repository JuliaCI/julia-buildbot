reload_scheduler = schedulers.AnyBranchScheduler(name="Buildbot Auto reload", change_filter=util.ChangeFilter(project='JuliaCI/julia-buildbot', branch=['buildog']), builderNames=["auto_reload"], treeStableTimer=1)
c['schedulers'].append(reload_scheduler)


# Steps to build a `make binary-dist` tarball that should work on just about every linux ever
reload_factory = util.BuildFactory()
reload_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present)
    steps.MasterShellCommand(
        name="Reload buildbot configuration",
        command=["/bin/sh", "-c", "cd /buildbot; git pull && buildbot reconfig master && git log -1"],
        flunkOnFailure=True
    )
])


c['builders'].append(util.BuilderConfig(
    name="auto_reload",
    workernames=all_names,
    tags=["Utility"],
    factory=reload_factory
))


# Add a scheduler for building release candidates/triggering builds manually
force_reload_scheduler = schedulers.ForceScheduler(
    name="force_reload",
    label="Force Buildbot reconfig",
    builderNames=["auto_reload"],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Packaging"),
        )
    ],
    properties=[]
)
c['schedulers'].append(force_reload_scheduler)
