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
save("coveralls.jld", "results", results)
results=Codecov.process_folder("base")
save("codecov.jld", "results", results)
"""

merge_cov_cmd = """
using Coverage, CoverageBase, HDF5, JLD, Compat
cd(joinpath(CoverageBase.julia_top()))
coveralls_results = CoverageBase.merge_coverage(load("coveralls_noninlined.jld", "results"), load("coveralls_inlined.jld", "results"))
codecov_results = CoverageBase.merge_coverage(load("codecov_noninlined.jld", "results"), load("codecov_inlined.jld", "results"))

# Create git_info for Coveralls
git_info = @compat Dict(
    "branch" => Base.GIT_VERSION_INFO.branch,
    "remotes" => [
        @compat Dict(
            "name" => "origin",
            "url" => "https://github.com/JuliaLang/julia.git"
        )
    ],
    "head" => @compat Dict(
        "id" => Base.GIT_VERSION_INFO.commit,
        "message" => "%(prop:commitmessage)s",
        "committer_name" => "%(prop:commitname)s",
        "committer_email" => "%(prop:commitemail)s",
        "author_name" => "%(prop:authorname)s",
        "author_email" => "%(prop:authoremail)s",
    )
)

# Submit to Coveralls
ENV["REPO_TOKEN"] = ENV["COVERALLS_REPO_TOKEN"]
Coveralls.submit_token(coveralls_results, git_info)

# Submit to codecov
ENV["REPO_TOKEN"] = ENV["CODECOV_REPO_TOKEN"]
Codecov.submit_token(codecov_results)
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

    # Ensure CoverageBase is installed
    ShellCommand(
        name="Install hdf5",
        command=["sudo", "apt-get", "install", "-y", "hdf5-tools"],
    ),
    ShellCommand(
        name="Install CoverageBase",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", "Pkg.add(\"CoverageBase\")"],
    ),
    ShellCommand(
        name="Checkout master",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", "Pkg.checkout(\"CoverageBase\", \"master\")"],
    ),

    # Update packages
    ShellCommand(
        name="Update packages",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", "Pkg.update(); Pkg.build()"],
    ),

    # Test CoverageBase to make sure everything's on the up-and-up
    ShellCommand(
        name="Test CoverageBase.jl",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", "Pkg.test(\"CoverageBase\")"],
        haltOnFailure=True,
    ),

    # Run Julia, gathering coverage statistics and then analyzing them into a .jld file
    ShellCommand(
        name="Run inlined tests",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "--precompiled=no", "--code-coverage=all", "-e", run_coverage_cmd]
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
        name="Move coveralls.jld -> coveralls_inlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/coveralls.jld"), Interpolate("julia-%(prop:shortcommit)s/share/julia/coveralls_inlined.jld")]
    ),
    ShellCommand(
        name="Move codecov.jld -> codecov_inlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/codecov.jld"), Interpolate("julia-%(prop:shortcommit)s/share/julia/codecov_inlined.jld")]
    ),

    # Do the coverage stats for non-inlined tests now
    ShellCommand(
        name="Run non-inlined tests",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "--precompiled=no", "--code-coverage=all", "--inline=no", "-e", run_coverage_cmd],
        timeout=3600,
    ),
    ShellCommand(
        name="Gather non-inlined test results",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", analyze_cov_cmd]
    ),
    ShellCommand(
        name="Move coverage_coveralls.jld -> coverage_coveralls_noninlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage_coveralls.jld"), Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage_coveralls_noninlined.jld")]
    ),
    ShellCommand(
        name="Move coverage_codecov.jld -> coverage_codecov_noninlined.jld",
        command=["mv", Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage_codecov.jld"), Interpolate("julia-%(prop:shortcommit)s/share/julia/coverage_codecov_noninlined.jld")]
    ),

    # Merge final results and submit!
    ShellCommand(
        name="Merge and submit",
        command=[Interpolate("julia-%(prop:shortcommit)s/bin/julia"), "-e", Interpolate(merge_cov_cmd)],
        env={'COVERALLS_REPO_TOKEN':COVERALLS_REPO_TOKEN, 'CODECOV_REPO_TOKEN':CODECOV_REPO_TOKEN},
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
