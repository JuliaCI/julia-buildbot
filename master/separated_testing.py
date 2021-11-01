###############################################################################
# Define everything needed to do per-commit testing.  This is the "separted
# testing" that @staticfloat has been going on about for so many years...
###############################################################################

julia_testing_env = {
    "JULIA_TEST_MAXRSS_MB": util.Property('maxrss', default=None),
    "JULIA_TEST_NUM_CORES": util.Interpolate('%(prop:nthreads)s'),
}

@util.renderer
def run_julia_tests(props_obj):
    props = props_obj_to_dict(props_obj)
    # We run all tests, even the ones that require internet connectivity.  Note that
    # it appears the windows shell can't deal with newlines.  :/
    test_cmd = """include(joinpath(Sys.BINDIR, Base.DATAROOTDIR, "julia", "test", "choosetests.jl")); Base.runtests(append!(choosetests()[1], ["LibGit2/online"]); ncores=min(Sys.CPU_THREADS, 8, {nthreads}))""".format(**props)

    cmd = ["bin/julia", "-e", test_cmd]
    if is_windows(props_obj):
        # On windows, we have a special autodump script
        cmd = ["bin\\julia.exe", "autodump.jl", str(props["buildnumber"]), props["shortcommit"], "bin\\julia.exe", "-e", test_cmd]
    if is_linux(props_obj) and props_obj.getProperty('tar_arch') in ('x86_64',) and props_obj.getProperty('use_rr', default=True):
        # On x86_64 and i686 linux, we have a special rr capturing script
        cmd = ["bin/julia", "rr_capture.jl", str(props["buildnumber"]), props["shortcommit"], "bin/julia", "-e", test_cmd]

    return cmd

@util.renderer
def render_upload_debugging_files(props_obj):
    props = props_obj_to_dict(props_obj)
    upload_script = """
    # Skip files that are non-existent (e.g. if there ARE no `.dmp` files)
    shopt -s nullglob
    for f in /tmp/julia_dumps/{os_name}{bits}/{buildnumber}/*; do
        path="{os_name}{bits}/{buildnumber}/$(basename "$f")"
        echo "uploading $(basename $f) to https://julialang-dumps.s3.amazonaws.com/$path"
        aws s3 cp "$f" "s3://julialang-dumps/$path" --quiet --acl public-read && rm -f "$f"
    done
    rm -rf /tmp/julia_dumps/{os_name}{bits}/{buildnumber}
    """.format(**props)
    return ["bash", "-c", upload_script]

# Steps to download a linux tarball, extract it and run tests on it
julia_testing_factory = util.BuildFactory()
julia_testing_factory.useProgress = True
julia_testing_factory.addSteps([
    # Clean the place out from previous runs
    steps.ShellCommand(
        name="clean it out",
        command=["sh", "-c", "rm -rf *"],
        flunkOnFailure=False,
    ),

    # Download the appropriate tarball and extract it
    steps.ShellCommand(
        name="Download Julia",
        command=download_julia,
    ),

    # Deploy helper functions
    steps.FileDownload(
        name="Deploy autodump.jl",
        mastersrc="../commands/autodump.jl",
        workerdest="autodump.jl",
        doStepIf=is_windows,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),
    steps.FileDownload(
        name="Deploy rr_capture.jl",
        mastersrc="../commands/rr_capture.jl",
        workerdest="rr_capture.jl",
        doStepIf=is_linux,
        hideStepIf=lambda results, s: results==SKIPPED,
    ),

    # Run tests!
    steps.ShellCommand(
        name="Run tests",
        command=run_julia_tests,
        haltOnFailure=True,
        # Fail out if 122 minutes have gone by with nothing printed to stdout
        # NOTE: Windows buildbots have a separate timeout of 2 hours total (regardless of stdout activity)
        # enforced by the autodump script.  We should eventually move everything over to that.
        timeout=122*60,
        # Kill everything if the overall job has taken more than 4 hours
        maxTime=60*60*4,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
        env=julia_testing_env,
    ),

    # Promote from pretesting to a nightly if it worked!
    steps.MasterShellCommand(
        name="Promote on AWS",
        command=render_promotion_command,
        haltOnFailure=True,
        doStepIf=should_promote,
    ),
    steps.MasterShellCommand(
        name="Promote on AWS",
        command=render_majmin_promotion_command,
        haltOnFailure=True,
        doStepIf=should_promote,
    ),
    steps.MasterShellCommand(
        name="Promote on AWS (latest)",
        command=render_latest_promotion_command,
        haltOnFailure=True,
        doStepIf=should_promote_latest,
    ),

    # Trigger a build of a non-assert version if the assert version finished properly
    steps.Trigger(
        schedulerNames=["Julia CI (non-assert build)"],
        set_properties={
            'assert_build': False,
        },
        waitForFinish=False,
        doStepIf=is_assert_nightly,
    ),

    # Upload and delete `.dmp` if they exist!
    steps.MultipleFileUpload(
        workersrcs=["dumps/*"],
        masterdest=util.Interpolate("/tmp/julia_dumps/%(prop:os_name)s%(prop:bits)s/%(prop:buildnumber)s"),
        glob=True,
        alwaysRun=True,
    ),

    steps.MasterShellCommand(
        name="Upload debugging files",
        command=render_upload_debugging_files,
        alwaysRun=True,
    ),
])

for builder, workers in builder_mapping.items():
    tester_name = "tester_%s"%(builder)
    # Add a dependent scheduler for running tests after we build tarballs
    c['schedulers'].append(schedulers.Triggerable(
        name="Julia CI (%s testing)"%(builder),
        builderNames=[tester_name],
    ))

    # Add testing builders
    c['builders'].append(util.BuilderConfig(
        name=tester_name,
        workernames=["tabularasa_"+w for w in workers],
        collapseRequests=False,
        tags=["Testing"],
        factory=julia_testing_factory,
    ))


c['schedulers'].append(schedulers.ForceScheduler(
    name="force_test",
    label="Force test build",
    builderNames=["tester_%s"%(k) for k in builder_mapping.keys()],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Coverage"),
        )
    ],
    properties=[
        util.StringParameter(
            name="download_url",
            size=60,
            default="https://julialangnightlies-s3.julialang.org/bin/linux/x64/julia-latest-linux64.tar.gz"
        ),
        util.BooleanParameter(name="use_rr", label="Use RR on linux{32,64} when running", default=True),
        util.StringParameter(
            name="shortcommit",
            size=10,
        ),
        util.StringParameter(
            name="majmin",
            size=3,
            default="1.4",
        )
    ]
))
