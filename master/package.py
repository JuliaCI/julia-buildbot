julia_package_env = {
    'CFLAGS': None,
    'CPPFLAGS': None,
    'LLVM_CMAKE': util.Property('llvm_cmake', default=None),

    # On platforms that use jemalloc, we can ask it to fill all allocated and
    # freed memory with junk, to ensure that we crash often if we attempt to
    # use memory after freeing it.
    'MALLOC_CONF': 'junk:true',
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

    # Add LLVM and Julia assertion flags if we're doing an assert build
    steps.SetProperty(
        name="Set assertion make flags",
        property="flags",
        value=util.Interpolate("%(prop:flags)s LLVM_ASSERTIONS=1 FORCE_ASSERTIONS=1"),
        doStepIf=lambda step: step.getProperty('assert_build'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    steps.SetProperty(
        name="Set BinaryBuilder LLVM flag",
        property="flags",
        value=util.Interpolate("%(prop:flags)s USE_BINARYBUILDER_LLVM=1"),
        doStepIf=lambda step: step.getProperty('use_bb_llvm'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
    
    steps.SetProperty(
        name="Set BinaryBuilder OpenBLAS flag",
        property="flags",
        value=util.Interpolate("%(prop:flags)s USE_BINARYBUILDER_OPENBLAS=1"),
        doStepIf=lambda step: step.getProperty('use_bb_openblas'),
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    # Recursive `git clean` on windows is very slow. It is faster to
    # wipe the dir and reset it. Important is that we don't delete our
    # `.git` folder
    steps.ShellCommand(
        name="[Win] wipe state",
        command=["/bin/sh", "-c", "cmd /c del /s /q *"],
        flunkOnFailure = False,
        doStepIf=is_windows,
        hideStepIf=lambda results, s: results==SKIPPED,
        env=julia_package_env,
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
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s %(prop:extra_make_flags)s win-extras")],
        haltOnFailure = True,
        doStepIf=is_windows,
        hideStepIf=lambda results, s: results==SKIPPED,
        env=julia_package_env,
    ),

    # Make release and debug simultaneously.  Once upon a time this caused
    # problems on Windows, let's try it again.
    steps.ShellCommand(
        name="make release/debug",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s release debug")],
        haltOnFailure = True,
        timeout=3600,
        env=julia_package_env,
    ),

    # Get info about ccache
    steps.ShellCommand(
        name="ccache stats",
        command=["/bin/sh", "-c", "ccache -s"],
        flunkOnFailure=False,
        env=julia_package_env,
    ),

    # Get build stats
    steps.ShellCommand(
        name="build stats",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s %(prop:extra_make_flags)s build-stats")],
        flunkOnFailure=False,
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
        command=[util.Interpolate("%(prop:make_cmd)s"), "print-JULIA_BINARYDIST_FILENAME"],
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
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s %(prop:flags)s %(prop:extra_make_flags)s binary-dist")],
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
        hideStepIf=lambda results, s: results==SKIPPED,
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
            'assert_build': util.Property('assert_build'),
            'upload_filename': util.Property('upload_filename'),
            'commitmessage': util.Property('commitmessage'),
            'commitname': util.Property('commitname'),
            'commitemail': util.Property('commitemail'),
            'authorname': util.Property('authorname'),
            'authoremail': util.Property('authoremail'),
            'shortcommit': util.Property('shortcommit'),
            'scheduler': util.Property('scheduler'),
        },
        waitForFinish=False,
    ),
])

# Build a builder-worker mapping based off of the parent mapping in inventory.py
packager_mapping = {("package_" + k): v for k, v in builder_mapping.iteritems()}

# This is the CI scheduler, where we build an assert build and test it
ci_scheduler = schedulers.AnyBranchScheduler(
    name="Julia testing build",
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia','staticfloat/julia'],
    ),
    builderNames=packager_mapping.keys(),
    treeStableTimer=1,
    properties={
        "assert_build": True,
    },
)
c['schedulers'].append(ci_scheduler)

# Add workers for these jobs
for packager, workers in packager_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=workers,
        collapseRequests=False,
        tags=["Packaging"],
        factory=julia_package_factory,
    ))

# Add a scheduler for building release candidates/triggering builds manually
force_build_scheduler = schedulers.ForceScheduler(
    name="package",
    label="Force build/packaging",
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
        util.StringParameter(
            name="extra_make_flags",
            label="Extra Make Flags",
            size=30,
            default="",
        ),
        util.BooleanParameter(
            name="assert_build",
            label="Build with Assertions",
            default=False,
        ),
        util.BooleanParameter(
            name="use_bb_llvm",
            label="Use BinaryBuilder LLVM",
            default=True,
        ),
        util.BooleanParameter(
            name="use_bb_openblas",
            label="Use BinaryBuilder OpenBLAS",
            default=True,
        ),
    ],
)
c['schedulers'].append(force_build_scheduler)
