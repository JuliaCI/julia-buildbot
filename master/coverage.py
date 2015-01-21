###############################################################################
# Define everything needed to do per-commit coverage testing on Linux
###############################################################################

# Add a dependent scheduler for running coverage after we build tarballs
julia_coverage_builders = ["coverage_ubuntu14.04-x64"]
julia_coverage_scheduler = Triggerable(name="Julia Coverage Testing", builderNames=julia_coverage_builders)
c['schedulers'].append(julia_coverage_scheduler)

run_coverage_cmd = """
import CoverageBase
using Base.Test
CoverageBase.runtests(CoverageBase.testnames())
"""

analyze_cov_cmd = """
import CoverageBase
using Coverage, HDF5, JLD
cd(joinpath(CoverageBase.julia_top()))
results=Coveralls.process_folder("base")
save("coverage.jld", "results", results)
"""

merge_cov_cmd = """
using Coverage, CoverageBase, HDF5, JLD
r1 = load("coverage_noninlined.jld", "results")
r2 = load("coverage_inlined.jld", "results")
r = CoverageBase.merge_coverage(r1, r2)
Coveralls.submit_token(r)
"""

# Steps to download a linux tarball, extract it, run coverage on it, and upload coverage stats
julia_coverage_factory = BuildFactory()
julia_coverage_factory.useProgress = True
julia_coverage_factory.addSteps([
    # Clean the place out from previous runs
    ShellCommand(
        name="clean it out",
        command=["/bin/bash", "-c", "rm -rf *"]
    ),

    # Download the latest tarball and extract it
    ShellCommand(
        name="download/extract tarball",
        command=["/bin/bash", "-c", Interpolate("curl -L %(prop:url)s | tar zx")],
    ),

    # Remove sys.so
    ShellCommand(
        name="Delete sys.so",
        command=["rm", "-f", Interpolate("julia-%(prop:shortcommit)s/lib/julia/sys.so")],
    ),

    # Run Julia, gathering coverage statistics and then analyzing them into a .jld file
    ShellCommand(
        name="Run inlined tests",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "--code-coverage=all", "-e", run_coverage_cmd]
    ),
    ShellCommand(
        name="Gather inlined test results",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", analyze_cov_cmd]
    ),

    # Clear out all .cov files, so that we can run the non-inlined tests without fear of interference
    ShellCommand(
        name="Clean out all .cov files",
        command=["/bin/bash", "-c", "find . -name *.cov | xargs rm -f"]
    ),
    ShellCommand(
        name="Move coverage.jld -> coverage_inlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage.jld"), "coverage_inlined.jld"]
    ),

    # Do the coverage stats for non-inlined tests now
    ShellCommand(
        name="Run non-inlined tests",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "--code-coverage=all", "--inline=no", "-e", run_coverage_cmd]
    ),
    ShellCommand(
        name="Gather non-inlined test results",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", analyze_cov_cmd]
    ),
    ShellCommand(
        name="Move coverage.jld -> coverage_noninlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage.jld"), "coverage_noninlined.jld"]
    ),

    # Merge final results and submit!
    ShellCommand(
        name="Merge and submit",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", merge_cov_cmd],
        env={'REPO_TOKEN':COVERAGE_REPO_TOKEN},
        logEnviron=False,
    ),
])


# Add coverage builders
c['builders'].append(BuilderConfig(
    name="coverage_ubuntu14.04-x64",
    slavenames=["ubuntu14.04-x64"],
    category="Coverage",
    factory=julia_coverage_factory
))
