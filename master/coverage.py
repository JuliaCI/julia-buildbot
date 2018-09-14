###############################################################################
# Define everything needed to do per-commit coverage testing on Linux
###############################################################################

run_coverage_cmd = """
using CoverageBase, Compat, Compat.Test
CoverageBase.runtests(CoverageBase.testnames())
"""

analyse_and_submit_cov_cmd = """
using Coverage, CoverageBase, Compat

cd(joinpath(CoverageBase.julia_top()))
results = Coverage.process_folder("base")
if isdefined(CoverageBase.BaseTestRunner, :STDLIBS)
    for stdlib in CoverageBase.BaseTestRunner.STDLIBS
        append!(results, Coverage.process_folder("site/v$(VERSION.major).$(VERSION.minor)/$stdlib/src"))
    end
end

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
        "message" => "%(prop:commitmessage)s",
        "committer_name" => "%(prop:commitname)s",
        "committer_email" => "%(prop:commitemail)s",
        "author_name" => "%(prop:authorname)s",
        "author_email" => "%(prop:authoremail)s",
    )
)

# Submit to Coveralls
ENV["REPO_TOKEN"] = ENV["COVERALLS_REPO_TOKEN"]
Coveralls.submit_token(results, git_info)
delete!(ENV, "REPO_TOKEN")

# Create git_info for codecov
git_info = Any[
    :branch => Base.GIT_VERSION_INFO.branch,
    :commit => Base.GIT_VERSION_INFO.commit,
    :token => ENV["CODECOV_REPO_TOKEN"],
    ]

# Submit to codecov
Codecov.submit_generic(results; git_info...)
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
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "Pkg.update(); Pkg.build()"],
    ),

    # Install Coverage, CoverageBase
    steps.ShellCommand(
        name="Install Coverage and checkout latest master",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "Pkg.add(\"Coverage\"); Pkg.checkout(\"Coverage\", \"master\")"],
    ),
    steps.ShellCommand(
        name="Install CoverageBase and checkout latest master",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "Pkg.add(\"CoverageBase\"); Pkg.checkout(\"CoverageBase\", \"master\")"],
    ),

    # Test CoverageBase to make sure everything's on the up-and-up
    steps.ShellCommand(
        name="Test CoverageBase.jl",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "Pkg.test(\"CoverageBase\")"],
        haltOnFailure=True,
    ),

    # Run Julia, gathering coverage statistics
    steps.ShellCommand(
        name="Run inlined tests",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "--sysimage-native-code=no", "--code-coverage=all", "-e", run_coverage_cmd],
        timeout=3600,
    ),
    steps.ShellCommand(
        name="Run non-inlined tests",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "--sysimage-native-code=no", "--code-coverage=all", "--inline=no", "-e", run_coverage_cmd],
        timeout=7200,
    ),
    #submit the results!
    steps.ShellCommand(
        name="Gather test results and Submit",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", util.Interpolate(analyse_and_submit_cov_cmd)],
        env={'COVERALLS_REPO_TOKEN':COVERALLS_REPO_TOKEN, 'CODECOV_REPO_TOKEN':CODECOV_REPO_TOKEN},
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
