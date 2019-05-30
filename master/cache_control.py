nuke_factory = util.BuildFactory()
nuke_factory.useProgress = True
nuke_factory.addSteps([
    steps.ShellCommand(
        name="Clear SRCCACHE",
        command=["/bin/sh", "-c", "rm -rf /tmp/srccache/*"],
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
        command=["/bin/sh", "-c", "rm -rf ../../package_*"],
        flunkOnFailure=False,
        doStepIf=lambda step: step.getProperty('clear_julia_package_repo'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
])

all_buildworkers = [n for n in all_names if not "tabularasa" in n]
for worker in all_buildworkers:
    c['schedulers'].append(schedulers.Triggerable(
        name="nuke_%s"%(worker),
        builderNames=["nuke_%s"%(worker)],
    ))

    c['builders'].append(util.BuilderConfig(
        name="nuke_%s"%(worker),
        workernames=[worker],
        collapseRequests=False,
        tags=["Cleaning"],
        factory=nuke_factory,
    ))

nuke_all_factory = util.BuildFactory()
nuke_all_factory.useProgress = True
nuke_all_steps = []
for worker in all_buildworkers:
    nuke_all_steps += [
        steps.Trigger(
            schedulerNames=["nuke_%s"%(worker)],
            waitForFinish=False,
            set_properties={k : util.Property(k) for k in ["clear_srccache", "clear_ccache", "clear_julia_package_repo"]},
        ),
    ]
c['builders'].append(util.BuilderConfig(
    name="nuke_all",
    workernames=[n for n in all_names],
    collapseRequests=True,
    tags=["Cleaning"],
    factory=nuke_all_factory,
))
nuke_all_factory.addSteps(nuke_all_steps)

c['schedulers'].append(schedulers.ForceScheduler(
    name = "nuke",
    label = "Clear all caches",
    builderNames = ["nuke_all"],
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
