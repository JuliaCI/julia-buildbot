# Add a manual scheduler for building release candidates
rc_scheduler = schedulers.ForceScheduler(
    name="force_rc",
    label="Force rc build",
    builderNames=["package_osx64", "package_win64", "package_win32", "package_linux64", "package_linux32", "package_linuxarmv7l", "package_linuxppc64le"],
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
c['schedulers'].append(rc_scheduler)
