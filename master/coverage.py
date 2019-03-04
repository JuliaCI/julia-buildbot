###############################################################################
# Define everything needed to do per-commit coverage testing on Linux
###############################################################################
import os

run_coverage_cmd = """
using Pkg
Pkg.activate("CoverageBase")
using CoverageBase
CoverageBase.runtests(CoverageBase.testnames())
"""

analyse_and_submit_cov_cmd = """
using Pkg
Pkg.activate("CoverageBase")
using Coverage, CoverageBase

# Process code-coverage files
results = Coverage.LCOV.readfolder(r"%(prop:juliadir)s/LCOV")
results = merge_coverage_counts(results, filter!(
    let prefixes = (joinpath("base", ""),
                    joinpath("stdlib", ""))
        c -> any(p -> startswith(c.filename, p), prefixes)
    end,
    results))
CoverageBase.fixpath!(results)
CoverageBase.readsource!(results)
#Coverage.amend_coverage_from_src!(results)

# Create git_info for codecov
git_info = Any[
    :branch => Base.GIT_VERSION_INFO.branch,
    :commit => Base.GIT_VERSION_INFO.commit,
    :token => ENV["CODECOV_REPO_TOKEN"],
    ]

# Submit to codecov
Codecov.submit_generic(results; git_info...)

# Create git_info for Coveralls
git_info = Dict(
    "branch" => Base.GIT_VERSION_INFO.branch,
    "remotes" => [
        Dict(
            "name" => "origin",
            "url" => "https://github.com/JuliaLang/julia.git"
        )
    ],
    "head" => Dict(
        "id" => Base.GIT_VERSION_INFO.commit,
        "message" => r"%(prop:commitmessage)s",
        "committer_name" => r"%(prop:commitname)s",
        "committer_email" => r"%(prop:commitemail)s",
        "author_name" => r"%(prop:authorname)s",
        "author_email" => r"%(prop:authoremail)s",
    )
)

# Submit to Coveralls
Coveralls.submit_local(results, git_info)
"""

# Steps to download a linux tarball, extract it, run coverage on it, and upload coverage stats
julia_coverage_factory = util.BuildFactory()
julia_coverage_factory.useProgress = True
julia_coverage_factory.addSteps([
    # Clean the place out from previous runs
    steps.ShellCommand(
        name="clean it out",
        command=["/bin/sh", "-c", "rm -rf *"]
    ),

    # Download the appropriate tarball and extract it
    steps.ShellCommand(
        name="download/extract tarball",
        command=["/bin/sh", "-c", util.Interpolate("curl -L %(prop:download_url)s | tar zx")],
    ),

    # Find Julia directory (so we don't have to know the shortcommit)
    steps.SetPropertyFromCommand(
        name="Find Julia executable",
        command=["/bin/sh", "-c", "echo julia-*"],
        property="juliadir"
    ),

    # Update packages
    steps.ShellCommand(
        name="Update packages",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.update(); Pkg.build()"],
    ),

    # Install Coverage, CoverageBase
    steps.ShellCommand(
        name="Install Coverage and checkout latest master",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.add(Pkg.PackageSpec(name=\"Coverage\", rev=\"master\"))"],
    ),
    steps.ShellCommand(
        name="Install CoverageBase and checkout latest master",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.add(Pkg.PackageSpec(name=\"CoverageBase\", rev=\"master\"))"],
    ),

    # Test CoverageBase to make sure everything's on the up-and-up
    steps.ShellCommand(
        name="Test CoverageBase.jl",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.test(\"CoverageBase\")"],
        haltOnFailure=True,
    ),

    # Run Julia, gathering coverage statistics
    steps.MakeDirectory(dir=util.Interpolate("mkdir %(prop:juliadir)s/LCOV")),
    steps.ShellCommand(
        name="Run tests",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"),
                 "--sysimage-native-code=no", util.Interpolate("--code-coverage=%(prop:juliadir)s/LCOV/cov-%%p.info"),
                 "-e", run_coverage_cmd],
        timeout=3600,
    ),
    #steps.ShellCommand(
    #    name="Run non-inlined tests",
    #    command=[util.Interpolate("%(prop:juliadir)s/bin/julia"),
    #             "--sysimage-native-code=no", util.Interpolate("--code-coverage=%(prop:juliadir)s/LCOV/cov-%%p.info"), "--inline=no",
    #             "-e", run_coverage_cmd],
    #    timeout=7200,
    #),
    #submit the results!
    steps.ShellCommand(
        name="Gather test results and Submit",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", util.Interpolate(analyse_and_submit_cov_cmd)],
        env={'COVERALLS_TOKEN':COVERALLS_REPO_TOKEN, 'CODECOV_REPO_TOKEN':CODECOV_REPO_TOKEN},
        logEnviron=False,
    ),
])


# Add a dependent scheduler for running coverage after we build tarballs
julia_coverage_builders = ["coverage_ubuntu16_04-x64"]
julia_coverage_scheduler = schedulers.Triggerable(name="Julia Coverage Testing", builderNames=julia_coverage_builders)
c['schedulers'].append(julia_coverage_scheduler)

c['schedulers'].append(schedulers.ForceScheduler(
    name="force_coverage",
    label="Force coverage build",
    builderNames=julia_coverage_builders,
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
    ]
))

# Add coverage builders
c['builders'].append(util.BuilderConfig(
    name="coverage_ubuntu16_04-x64",
    workernames=["tabularasa_ubuntu16_04-x64"],
    tags=["Coverage"],
    factory=julia_coverage_factory
))
