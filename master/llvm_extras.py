## This file used for building llvm_extras tarballs
llvm_extras_env = {
    'CFLAGS': None,
    'CPPFLAGS': None,
    'LLVM_CMAKE': util.Property('llvm_cmake', default=None),
}

# Steps to build an "llvm-extras" tarball, useful for things like LLVM.jl
llvm_extras_factory = util.BuildFactory()
llvm_extras_factory.useProgress = True
llvm_extras_factory.addSteps([
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
        mode='incremental',
        method='clean',
        submodules=True,
        clobberOnFailure=True,
        progress=True
    ),

    # make clean first
    steps.ShellCommand(
        name="make cleanall",
        command=["/bin/bash", "-c", util.Interpolate("make %(prop:flags)s BUILD_LLVM_CLANG=1 %(prop:extra_make_flags)s -C deps distcleanall")],
        env=llvm_extras_env,
    ),

    # Our llvm build process fails to properly create `$(build_libdir)` before installing llvm, so let's do it first
    steps.ShellCommand(
        name="make",
        command=["/bin/bash", "-c", util.Interpolate("make -j3 %(prop:flags)s BUILD_LLVM_CLANG=1 %(prop:extra_make_flags)s usr/lib")],
        haltOnFailure = True,
        timeout=3600,
        env=llvm_extras_env,
    ),

    # Make, forcing some degree of parallelism to cut down compile times
    steps.ShellCommand(
        name="make",
        command=["/bin/bash", "-c", util.Interpolate("make -j3 %(prop:flags)s BUILD_LLVM_CLANG=1 %(prop:extra_make_flags)s -C deps install-llvm")],
        haltOnFailure = True,
        timeout=3600,
        env=llvm_extras_env,
    ),

    # Set a bunch of properties that are useful down the line
    steps.SetPropertyFromCommand(
        name="Get shortcommit",
        command=["git", "log", "-1", "--pretty=format:%h"],
        property="shortcommit",
        want_stderr=False
    ),

    # Make binary-dist to package it up
    steps.ShellCommand(
        name="make binary-dist",
        command=["tar", "zcvf", util.Interpolate("llvm_extras-%(prop:shortcommit)s.tar.gz"), "usr"],
        haltOnFailure = True,
        timeout=3600,
    ),

    # Transfer the result to the buildmaster for uploading to AWS
    steps.MasterShellCommand(
        name="Make llvm_extras directory",
        command=["mkdir", "-p", "/tmp/llvm_extras"]
    ),

    steps.FileUpload(
        workersrc=util.Interpolate("llvm_extras-%(prop:shortcommit)s.tar.gz"),
        masterdest=util.Interpolate("/tmp/llvm_extras/llvm_extras-%(prop:shortcommit)s.tar.gz")
    ),

    # Upload it to AWS and cleanup the master!
    steps.MasterShellCommand(
        name="Upload to AWS",
        command=[
            "/bin/bash",
            "-c",
            util.Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julialangmirror/llvm_extras-%(prop:shortcommit)s.tar.gz /tmp/llvm_extras/llvm_extras-%(prop:shortcommit)s.tar.gz")
        ],
        haltOnFailure=True
    ),
    steps.MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", util.Interpolate("/tmp/llvm_extras/llvm_extras-%(prop:shortcommit)s.tar.gz")]
    ),
])

# Build a builder-worker mapping based off of the parent mapping in inventory.py
llvm_extras_mapping = {("llvm_extras_" + k): v for k, v in builder_mapping.iteritems()}

for packager, worker in llvm_extras_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=[worker],
        collapseRequests=False,
        tags=["llvm_extras"],
        factory=llvm_extras_factory
    ))


# Add a scheduler for triggering builds manually
force_llvm_extras_scheduler = schedulers.ForceScheduler(
    name="package_llvm_extras",
    label="Force llvm_extras build/packaging",
    builderNames=llvm_extras_mapping.keys(),
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
c['schedulers'].append(force_llvm_extras_scheduler)
