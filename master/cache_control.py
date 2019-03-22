nuke_factory = util.BuildFactory()
nuke_factory.useProgress = True
nuke_factory.addSteps([
    steps.ShellCommand(
        name="Clear SRCCACHE",
        command=["/bin/bash", "-c", "rm -rf /tmp/srccache/*"],
        flunkOnFailure=False,
        doStepIf=lambda step: step.getProperty('clear_srccache'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    steps.ShellCommand(
        name="Clear ccache cache",
        command=["ccache", "-C"],
        flunkOnFailure=False,
        doStepIf=lambda step: step.getProperty('clear_ccache'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    steps.ShellCommand(
        name="Clear Julia .git folder",
        command=["/bin/bash", "-c", "rm -rf ../../package_*"],
        flunkOnFailure=False,
        doStepIf=lambda step: step.getProperty('clear_julia_package_repo'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
])

c['schedulers'].append(schedulers.ForceScheduler(
    name = "clear_cache",
    label = "Clear caches",
    builderNames = ["nuke_" + k for k in builder_mapping.keys()],
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
    properties = [
        util.BooleanParameter(
            name="clear_srccache",
            label="Clear SRCCACHE",
            default=True,
        ),
        util.BooleanParameter(
            name="clear_ccache",
            label="Clear ccache cache",
            default=False,
        ),
        util.BooleanParameter(
            name="clear_julia_package_repo",
            label="Clear Julia .git folder",
            default=True,
        ),
    ]
))

# Add workers for these jobs
for builder, workers in builder_mapping.items():
    c['builders'].append(util.BuilderConfig(
        name="nuke_" + builder,
        workernames=workers,
        collapseRequests=False,
        tags=["Cleaning"],
        factory=nuke_factory,
    ))