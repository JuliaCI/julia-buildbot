julia_package_env = {
    'CFLAGS': None,
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
        command=["git", "fetch", "--tags", "--all", "--force"],
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
        name="Set BinaryBuilder flag",
        property="flags",
        value=util.Interpolate("%(prop:flags)s USE_BINARYBUILDER=%(prop:use_bb:#?:1:0)s"),
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
        progress=True,
        retryFetch=True,
        getDescription={'tags': True},
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

    # Make release (we don't automatically build debug)
    steps.ShellCommand(
        name="make release",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s release")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 10 hours
        maxTime=60*60*10,
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
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 10 hours
        maxTime=60*60*10,
        env=julia_package_env,
    ),

    # Build .app on macOS
    steps.ShellCommand(
        name="make .app",
        command=["/bin/sh", "-c", util.Interpolate("~/unlock_keychain.sh && make %(prop:flags)s %(prop:extra_make_flags)s app")],
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
packager_mapping = {("package_" + k): v for k, v in builder_mapping.items()}

def julia_ci_filter(c):
    # Build pull requests and pushes to `master`/`release-*`
    allow_branch = lambda b: b == 'master' or b.startswith('release-')
    return (c.project in ['JuliaLang/julia']) and (c.category == 'pull' or allow_branch(c.branch))

# This is the CI scheduler, where we build an assert build and test it
c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia CI (assert build)",
    change_filter=util.ChangeFilter(filter_fn=julia_ci_filter),
    builderNames=[k for k in packager_mapping.keys()],
    treeStableTimer=1,
    properties={
        "assert_build": True,

        # Default to using BB
        'use_bb': True,
    },
))

# Add a dependent scheduler for non-assert after we build tarballs
c['schedulers'].append(schedulers.Triggerable(
    name="Julia CI (non-assert build)",
    builderNames=[k for k in packager_mapping.keys()],
    properties={
        "assert_build": False,

        # Default to using BB
        'use_bb': True,
    }
))


# Add workers for these jobs
for packager, workers in packager_mapping.items():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=workers,
        collapseRequests=False,
        tags=["Packaging"],
        factory=julia_package_factory,
    ))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="package",
    label="Force build/packaging",
    builderNames=[k for k in packager_mapping.keys()],
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
            name="use_bb",
            label="Use BinaryBuilder dependencies",
            default=True,
        ),
    ],
))




## We're also going to add a force-only scheduler that just triggers package
#  jobs on all our platforms:
package_all_factory = util.BuildFactory()
package_all_factory.useProgress = True
package_all_steps = []
for packager, workers in packager_mapping.items():
    package_all_steps += [
        steps.Trigger(
            schedulerNames=[packager],
            waitForFinish=False,
            set_properties={k : util.Property(k) for k in ["extra_make_flags", "assert_build", "use_bb"]},
        ),
    ]
c['builders'].append(util.BuilderConfig(
    name="package_all",
    workernames=[n for n in all_names],
    collapseRequests=True,
    tags=["Packaging"],
    factory=package_all_factory,
))
package_all_factory.addSteps(package_all_steps)

c['schedulers'].append(schedulers.ForceScheduler(
    name = "package_all",
    label = "Package on all buildbots",
    builderNames = ["package_all"],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Cleaning"),
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
            name="use_bb",
            label="Use BinaryBuilder dependencies",
            default=True,
        ),
    ],
))

