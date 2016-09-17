# Add a manual scheduler for building release candidates
rc_scheduler = schedulers.ForceScheduler(
    name="rc build",
    builderNames=["package_osx10.9-x64", "package_win6.2-x64", "package_win6.2-x86", "package_tarball64", "package_tarball32", "package_tarballarm", "package_tarballppc64le"],
    reason=util.FixedParameter(name="reason", default=""),
    branch=util.FixedParameter(name="branch", default=""),
    repository=util.FixedParameter(name="repository", default=""),
    project=util.FixedParameter(name="project", default="Packaging"),
    properties=[
    ]
)
c['schedulers'].append(rc_scheduler)
