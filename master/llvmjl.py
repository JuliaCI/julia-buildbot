## This file used for building LLVM.jl deps/ tarballs

@util.renderer
def build_llvmjl(props_obj):
    props = props_obj_to_dict(props_obj)
    cmd = ["bin/julia", "-e"]

    if is_windows(props_obj):
        cmd[0] += ".exe"

    cmd += ["""
        ENV["JULIA_PKGDIR"] = ".";
        Pkg.init();
        try
            Pkg.add("LLVM", "{revision}");
        end
        
        # Fake our build directory target into here:
        ARGS[1] = abspath("./llvmjl_out");
        include(Pkg.dir("LLVM", "deps", "buildbot.jl"));
    """.format(**props).strip()]
    return cmd

llvmjl_factory = util.BuildFactory()
llvmjl_factory.useProgress = True
llvmjl_factory.addSteps([
    # Cleanup
    steps.ShellCommand(
        name="Cleanup",
        command=["rm", "-rf", "*"],
    ),

    # Download Julia
    steps.SetPropertyFromCommand(
        name="Download Julia",
        command=download_julia,
        property="julia_path",
    ),
    # Download llvm-extras
    steps.ShellCommand(
        name="Download llvm-extras",
        command=["bash", "-c", util.Interpolate("cd julia-*; curl -L 'https://s3.amazonaws.com/julialangmirror/llvm_extras-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz' | tar -zxv --strip-components=1")],
    ),

    # Invoke Julia to build LLVM
    steps.SetPropertyFromCommand(
        name="Install LLVM.jl",
        command=build_llvmjl,
        property="code_result",
    ),

    # Package up our ill-gotten goods
    steps.ShellCommand(
        name="Package LLVM.jl deps directory",
        command=["tar", "zcvf", util.Interpolate("llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz"), "-C", "llvmjl_out/"],
        haltOnFailure = True,
    ),

    # Transfer the result to the buildmaster for uploading to AWS
    steps.MasterShellCommand(
        name="Make llvm_jl directory",
        command=["mkdir", "-p", "/tmp/llvm_jl"]
    ),

    steps.FileUpload(
        workersrc=util.Interpolate("llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz"),
        masterdest=util.Interpolate("/tmp/llvm_jl/llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz")
    ),

    # Upload it to AWS and cleanup the master!
    steps.MasterShellCommand(
        name="Upload to AWS",
        command=[
            "/bin/bash",
            "-c",
            util.Interpolate("~/bin/try_thrice ~/bin/aws put --fail --public julialangmirror/llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz /tmp/llvm_jl/llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz")
        ],
        haltOnFailure=True
    ),
    steps.MasterShellCommand(
        name="Cleanup Master",
        command=["rm", "-f", util.Interpolate("/tmp/llvm_jl/llvmjl-%(prop:shortcommit)s-%(prop:os_name)s%(prop:bits)s.tar.gz")]
    ),
])

# Build a builder-worker mapping based off of the parent mapping in inventory.py
llvmjl_mapping = {("llvmjl_" + k): v for k, v in builder_mapping.iteritems()}

for packager, worker in llvmjl_mapping.iteritems():
    c['builders'].append(util.BuilderConfig(
        name=packager,
        workernames=[worker],
        collapseRequests=False,
        tags=["llvmjl"],
        factory=llvmjl_factory
    ))

# Add a scheduler for building tags of LLVM.jl
tag_llvmjl_scheduler = schedulers.AnyBranchScheduler(
    name="LLVM.jl deps packaging",
    change_filter=util.ChangeFilter(
        project=['maleadt/LLVM.jl', 'staticfloat/LLVM.jl'],
    ),
    builderNames=llvmjl_mapping.keys(),
    treeStableTimer=1,
    # Bake these properties in hard, we can always override with a force scheduler
    properties={
        'shortcommit': '903644385b',
        'majmin': '0.6',
    }
)
c['schedulers'].append(tag_llvmjl_scheduler)

# Add a scheduler for triggering builds manually
force_llvmjl_scheduler = schedulers.ForceScheduler(
    name="package_llvmjl",
    label="Force LLVM.jl deps packaging",
    builderNames=llvmjl_mapping.keys(),
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
        util.StringParameter(name="shortcommit", label="shortcommit (e.g. 1a2b3c4d)", size=15, default="903644385b"),
        util.StringParameter(name="majmin", label="majmin version (e.g. 0.6)", size=2, default="0.6"),
    ]
)
c['schedulers'].append(force_llvmjl_scheduler)
