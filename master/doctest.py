julia_doctest_factory = util.BuildFactory()
julia_doctest_factory.useProgress = True
julia_doctest_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present)
    steps.ShellCommand(
        name="git fetch",
        command=["git", "fetch", "--tags", "--all", "--force"],
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
        progress=True,
        retryFetch=True,
        getDescription={'--tags': True},
    ),

    # Make Julia itself
    steps.ShellCommand(
        name="make release",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s JULIA_PRECOMPILE=0 %(prop:flags)s %(prop:extra_make_flags)s release")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),

    steps.ShellCommand(
        name="make doctest",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C doc JULIA_PRECOMPILE=0 -j%(prop:nthreads)s %(prop:flags)s %(prop:extra_make_flags)s doctest=true")],
        haltOnFailure = True,
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 2 hours
        maxTime=60*60*2,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),

    steps.ShellCommand(
        name="make deploy",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C doc JULIA_PRECOMPILE=0 %(prop:flags)s %(prop:extra_make_flags)s deploy")],
        haltOnFailure=True,
        env={
            'DOCUMENTER_KEY': DOCUMENTER_KEY,
            'TRAVIS_PULL_REQUEST': 'false',
        },
        doStepIf=is_protected_pr,
    ),

    # Get JULIA_VERSION and JULIA_COMMIT from the build system
    steps.SetPropertyFromCommand(
        name="Get JULIA_VERSION",
        command=[util.Interpolate("%(prop:make_cmd)s"), "print-JULIA_VERSION"],
        extract_fn=lambda rc, stdout, stderr: {"JULIA_VERSION": stdout[stdout.find('=')+1:].strip()}
    ),
    steps.SetPropertyFromCommand(
        name="Get JULIA_COMMIT",
        command=[util.Interpolate("%(prop:make_cmd)s"), "print-JULIA_COMMIT"],
        extract_fn=lambda rc, stdout, stderr: {"JULIA_COMMIT": stdout[stdout.find('=')+1:].strip()}
    ),

    # We've already got Julia and the docs built; so let's build the source tarballs too
    steps.ShellCommand(
        name="make light-source-dist",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s JULIA_PRECOMPILE=0 USE_BINARYBUILDER=0 %(prop:flags)s %(prop:extra_make_flags)s light-source-dist")],
        haltOnFailure = True,
        doStepIf=is_protected_pr,
    ),
    steps.FileUpload(
        name="Upload light source tarball",
        workersrc=util.Interpolate("julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s.tar.gz"),
        masterdest=util.Interpolate("/tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s.tar.gz"),
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    steps.ShellCommand(
        name="make full-source-dist (without BB)",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s JULIA_PRECOMPILE=0 USE_BINARYBUILDER=0 %(prop:flags)s %(prop:extra_make_flags)s full-source-dist")],
        haltOnFailure = True,
        doStepIf=is_protected_pr,
    ),
    steps.FileUpload(
        name="Upload full source tarball",
        workersrc=util.Interpolate("julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full.tar.gz"),
        masterdest=util.Interpolate("/tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full.tar.gz"),
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    steps.ShellCommand(
        name="make full-source-dist (with BB)",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -j%(prop:nthreads)s JULIA_PRECOMPILE=0 USE_BINARYBUILDER=1 %(prop:flags)s %(prop:extra_make_flags)s full-source-dist")],
        haltOnFailure = True,
        doStepIf=is_protected_pr,
    ),
    steps.FileUpload(
        name="Upload full source+bb tarball",
        workersrc=util.Interpolate("julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full.tar.gz"),
        masterdest=util.Interpolate("/tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full+bb.tar.gz"),
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    # Sign and upload on the master
    steps.MasterShellCommand(
        name="gpg sign light source tarball on master",
        command=["sh", "-c", util.Interpolate("/root/sign_tarball.sh /tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s.tar.gz")],
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
    steps.MasterShellCommand(
        name="gpg sign full source tarball on master",
        command=["sh", "-c", util.Interpolate("/root/sign_tarball.sh /tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full.tar.gz")],
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
    steps.MasterShellCommand(
        name="gpg sign full+bb source tarball on master",
        command=["sh", "-c", util.Interpolate("/root/sign_tarball.sh /tmp/julia_package/julia-%(prop:JULIA_VERSION)s_%(prop:JULIA_COMMIT)s-full+bb.tar.gz")],
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
    steps.MasterShellCommand(
        name="Upload source tarballs to AWS",
        command=render_srcdist_upload_command,
        haltOnFailure=True,
        doStepIf=is_protected_pr,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
])

c['schedulers'].append(schedulers.AnyBranchScheduler(
    name="Julia Doctesting and source upload",
    change_filter=util.ChangeFilter(filter_fn=julia_branch_nonskip_filter),
    builderNames=["doctest_linux64"],
    treeStableTimer=1,
))

# Add workers for these jobs
c['builders'].append(util.BuilderConfig(
    name="doctest_linux64",
    workernames=builder_mapping["linux64"],
    collapseRequests=False,
    tags=["Packaging"],
    factory=julia_doctest_factory,
))

# Add a scheduler for building release candidates/triggering builds manually
c['schedulers'].append(schedulers.ForceScheduler(
    name="doctest",
    label="Force doctest",
    builderNames=["doctest_linux64"],
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
    ],
))
