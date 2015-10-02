###############################################################################
# Define everything needed to do per-commit performance tracking on Linux
###############################################################################

# Add a dependent scheduler for running coverage after we build tarballs
julia_perf_builders = ["perf_nanosoldier-x64"]
julia_perf_scheduler = Triggerable(name="Julia Performance Tracking", builderNames=julia_perf_builders)
c['schedulers'].append(julia_perf_scheduler)

c['schedulers'].append(ForceScheduler(
    name="perf run",
    builderNames=julia_perf_builders,
    reason=FixedParameter(name="reason", default=""),
    revision=FixedParameter(name="revision", default=""),
    branch=FixedParameter(name="branch", default=""),
    repository=FixedParameter(name="repository", default=""),
    project=FixedParameter(name="project", default="Coverage"),
    properties=[
        StringParameter(name="url", size=60, default="https://status.julialang.org/download/linux-x86_64"),
    ]
))

install_perf_cmd = """
Pkg.update()
try Pkg.clone("https://github.com/johnmyleswhite/Benchmarks.jl") end
try Pkg.clone("https://github.com/staticfloat/Perftests.jl") end
try Pkg.add("Compat") end
Pkg.resolve()
Pkg.build()
"""

run_perf_cmd = """
Pkg.test("Perftests")
"""

# Steps to download a linux tarball, extract it, run coverage on it, and upload coverage stats
julia_perf_factory = BuildFactory()
julia_perf_factory.useProgress = True
julia_perf_factory.addSteps([
    # Clean the place out from previous runs
    ShellCommand(
        name="clean it out",
        command=["/bin/bash", "-c", "rm -rf *"]
    ),

    # Download the appropriate tarball and extract it
    ShellCommand(
        name="download/extract tarball",
        command=["/bin/bash", "-c", Interpolate("curl -L %(prop:url)s | tar zx")],
    ),

    # Find Julia directory (so we don't have to know the shortcommit)
    SetPropertyFromCommand(
        name="Find Julia executable",
        command=["/bin/bash", "-c", "echo julia-*"],
        property="juliadir"
    ),

    # Update packages
    ShellCommand(
        name="Update packages",
        command=[Interpolate("%(prop:juliadir)s/bin/julia"), "-e", install_perf_cmd],
    ),

    # Run the actual perf tests to create the .csv files
    ShellCommand(
        name="Run perf tests",
        command=[Interpolate("%(prop:juliadir)s/bin/julia"), "-e", run_perf_cmd]
    ),
])


# Add coverage builders
c['builders'].append(BuilderConfig(
    name="perf_nanosoldier-x64",
    slavenames=["nanosoldier-x64"],
    category="Performance",
    factory=julia_perf_factory
))
