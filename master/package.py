julia_package_env = {
    'CFLAGS':None,
    'CPPFLAGS': None,
    'LLVM_CMAKE': util.Property('llvm_cmake', default=None),
}

# Steps to build a `make binary-dist` tarball that should work on just about every linux ever
julia_package_factory = util.BuildFactory()
julia_package_factory.useProgress = True
julia_package_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present)
    steps.ShellCommand(
        name="git fetch",
        command=["git", "fetch"],
        flunkOnFailure=False
    ),

    # Clone julia
    steps.Git(
        name="Julia checkout",
        repourl=util.Property('repository', default='git://github.com/JuliaLang/julia.git'),
        mode='full',
        method='fresh',
        submodules=True,
        clobberOnFailure=True,
        progress=True
    ),

    # Get win-extras files ready on windows
    steps.ShellCommand(
        name="make win-extras",
        command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s %(prop:extra_make_flags)s win-extras")],
        haltOnFailure = True,
        doStepIf=is_windows,
        env=julia_package_env,
    ),

    # Make, forcing some degree of parallelism to cut down compile times
    steps.ShellCommand(
        name="make release",
        command=["/bin/bash", "-c", util.Interpolate("make -j3 %(prop:flags)s %(prop:extra_make_flags)s release")],
        haltOnFailure = True,
        timeout=3600,
        env=julia_package_env,
    ),
    steps.ShellCommand(
        name="make debug",
        command=["/bin/bash", "-c", util.Interpolate("make -j3 %(prop:flags)s %(prop:extra_make_flags)s debug")],
        haltOnFailure = True,
        timeout=3600,
        env=julia_package_env,
    ),

    # Set a bunch of properties that are useful down the line
    steps.SetPropertyFromCommand(
        name="Get commitmessage",
        command=["git", "log", "-1", "--pretty=format:%s%n%cN%n%cE%n%aN%n%aE"],
        extract_fn=parse_git_log,
        want_stderr=False
    ),
    steps.SetPropertyFromCommand(
        name="Get julia version/shortcommit",
        command=make_julia_version_command,
        extract_fn=parse_julia_version,
        want_stderr=False
    ),
    steps.SetPropertyFromCommand(
        name="Get build artifact filename",
        command=["make", "print-JULIA_BINARYDIST_FILENAME"],
        property="artifact_filename",
    ),
    steps.SetPropertyFromCommand(
        name="Munge artifact filename",
        command=munge_artifact_filename,
        property="dummy",
    ),

    # Make binary-dist to package it up
    steps.ShellCommand(
        name="make binary-dist",
        command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s %(prop:extra_make_flags)s binary-dist")],
        haltOnFailure = True,
        timeout=3600,
        env=julia_package_env,
    ),

    # On OSX, deal with non-sf/consistent_distnames makefile nonsense by wrapping up all
    # the complexity into `render_make_app`.
    steps.ShellCommand(
        name="make .app",
        command=render_make_app,
        haltOnFailure = True,
        doStepIf=is_mac,
        env=julia_package_env,
    ),

    # Transfer the result to the buildmaster for uploading to AWS
    steps.MasterShellCommand(
        name="mkdir julia_package",
        command=["mkdir", "-p", "/tmp/julia_package"],
    ),

    steps.FileUpload(
        workersrc=util.Interpolate("%(prop:local_filename)s"),
        masterdest=util.Interpolate("/tmp/julia_package/%(prop:upload_filename)s"),
    ),

    # Upload it to AWS and cleanup the master!
    steps.MasterShellCommand(
        name="Upload to AWS",
        command=render_upload_command,
        haltOnFailure=True
    ),

    steps.MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", util.Interpolate("/tmp/julia_package/%(prop:upload_filename)s")],
    ),

    # Trigger a download of this file onto another worker for testing
    steps.Trigger(
        schedulerNames=[render_tester_name],
        set_properties={
            'download_url': render_pretesting_download_url,
            'majmin': util.Property('majmin'),
            'upload_filename': util.Property('upload_filename'),
            'commitmessage': util.Property('commitmessage'),
            'commitname': util.Property('commitname'),
            'commitemail': util.Property('commitemail'),
            'authorname': util.Property('authorname'),
            'authoremail': util.Property('authoremail'),
            'shortcommit': util.Property('shortcommit'),
        },
        waitForFinish=False,
    )
])

# Build a builder-worker mapping based off of the parent mapping in inventory.py
packager_mapping = {("package_" + k): v for k, v in builder_mapping.iteritems()}

# Add a few builders that don't exist in the typical mapping
#packager_mapping["build_ubuntu32"] = "ubuntu16_04-x86"
#packager_mapping["build_ubuntu64"] = "ubuntu16_04-x64"
#packager_mapping["build_centos64"] = "centos7_3-x64"

packager_scheduler = schedulers.AnyBranchScheduler(
    name="Julia Binary Packaging",
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia','staticfloat/julia'],
        # Only build `master` or `release-*`
        branch_fn=lambda b: b == "master" or b.startswith("release-")
    ),
    builderNames=packager_mapping.keys(),
    treeStableTimer=1
)
c['schedulers'].append(packager_scheduler)

for packager, worker in packager_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=[worker],
        collapseRequests=False,
        tags=["Packaging"],
        factory=julia_package_factory
    ))


# Add a scheduler for building release candidates/triggering builds manually
force_build_scheduler = schedulers.ForceScheduler(
    name="package",
    label="Force Julia build/packaging",
    builderNames=packager_mapping.keys(),
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
    properties=[
        util.StringParameter(name="extra_make_flags", label="Extra Make Flags", size=30, default=""),
    ]
)
c['schedulers'].append(force_build_scheduler)
