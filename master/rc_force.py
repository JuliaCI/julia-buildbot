# Add a manual scheduler for building release candidates
rc_scheduler = ForceScheduler(
    name="rc build",
    builderNames=["package_osx10.9-x64", "package_win6.2-x64", "package_win6.2-x86", "package_tarball64", "package_tarball32", "package_tarballarmv6"],
    reason=FixedParameter(name="reason", default=""),
    branch=FixedParameter(name="branch", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Packaging"),
    properties=[
    ]
)
c['schedulers'].append(rc_scheduler)
