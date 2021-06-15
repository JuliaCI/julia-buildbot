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

analyse_and_submit_cov_cmd = '''
using Pkg
Pkg.activate("CoverageBase")
using Coverage, CoverageBase
# Process code-coverage files
results = Coverage.LCOV.readfolder(raw"%(prop:juliadir)s/LCOV")
  # remove test/ files
filter!(results) do c
    !occursin("test/", c.filename)
end
  # turn absolute paths into relative, and add base/ to relative paths
CoverageBase.fixpath!(results)
results = Coverage.merge_coverage_counts(results)
  # pretty-print what we have got
sort!(results, by=c->c.filename)
for r in results
    cov, tot = get_summary(r)
    @info "Got coverage data for $(r.filename): $cov/$tot"
end
  # keep only files in stdlib/ and base/
let prefixes = (joinpath("base", ""),
                joinpath("stdlib", ""))
    filter!(results) do c
        any(p -> startswith(c.filename, p), prefixes)
    end
end
  # try to find these files, remove those that are not present
CoverageBase.readsource!(results)
filter!(results) do c
    if isempty(c.source)
        @info "File $(c.filename) not found"
        false
    else
        true
    end
end
  # add in any other files we discover
  # todo: extend Glob.jl to support these patterns (base/**/*.jl and stdlib/*/src/**/*.jl (except test/))
  # todo: consider also or instead looking at the Base._included_files list
allfiles_base = sort!(split(readchomp(Cmd(`find base -name '*.jl'`, dir=CoverageBase.fixabspath(""))), '\n'))
allfiles_stdlib = sort!(map(x -> "stdlib/" * x[3:end],
    split(readchomp(Cmd(`find . -name '*.jl' ! -path '*/test/*' ! -path '*/docs/*'`, dir=CoverageBase.fixabspath("stdlib/"))), '\n')))
allfiles = map(fn -> Coverage.FileCoverage(fn, read(CoverageBase.fixabspath(fn), String), Coverage.FileCoverage[]),
    [allfiles_base; allfiles_stdlib])
results = Coverage.merge_coverage_counts(results, allfiles)
length(results) == length(allfiles) || @warn "Got coverage for an unexpected file:" symdiff=symdiff(map(x -> x.filename, allfiles), map(x -> x.filename, results))
  # Drop external stdlibs (i.e. stdlibs that live in external repos):
let
    get_external_stdlib_prefixes = function (stdlib_dir)
        filename_list = filter(x -> isfile(joinpath(stdlib_dir, x)), readdir(stdlib_dir))
        # find all of the files like `Pkg.version`, `Statistics.version`, etc.
        regex_matches_or_nothing = match.(Ref(r"^([\w].*?)\.version$"), filename_list)
        regex_matches = filter(x -> x !== nothing, regex_matches_or_nothing)
        # get the names of the external stdlibs, like `Pkg`, `Statistics`, etc.
        external_stdlib_names = only.(regex_matches)
        prefixes = joinpath.(Ref(stdlib_dir), external_stdlib_names, Ref(""))
        # example of what `prefixes` might look like:
        # 2-element Vector{String}:
        # "stdlib/Pkg/"
        # "stdlib/Statistics/"
        return prefixes
    end
    # external_stdlib_prefixes = get_external_stdlib_prefixes("stdlib")
    external_stdlib_prefixes = String[
        "stdlib/ArgTools/",
        "stdlib/Downloads/",
        "stdlib/LibCURL/",
        "stdlib/NetworkOptions/",
        "stdlib/Pkg/",
        "stdlib/Statistics/",
        "stdlib/SuiteSparse/",
        "stdlib/Tar/",
    ]
    filter!(results) do c
        all(p -> !startswith(c.filename, p), external_stdlib_prefixes)
    end
    @info "" pwd() # debugging statement; remove later
    @info "" readdir(pwd()) # debugging statement; remove later
    @info "" first(readdir(pwd())) # debugging statement; remove later
    @info "" joinpath(pwd(), first(readdir(pwd()))) # debugging statement; remove later
    @info "" readdir(joinpath(pwd(), first(readdir(pwd())))) # debugging statement; remove later
end
  # attempt to improve accuracy of the results
foreach(Coverage.amend_coverage_from_src!, results)
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
        "message" => raw"""%(prop:commitmessage)s""",
        "committer_name" => raw"""%(prop:commitname)s""",
        "committer_email" => raw"""%(prop:commitemail)s""",
        "author_name" => raw"""%(prop:authorname)s""",
        "author_email" => raw"""%(prop:authoremail)s""",
    )
)
# Submit to Coveralls
Coveralls.submit_local(results, git_info)
'''

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
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.add(Pkg.PackageSpec(url=\"https://github.com/JuliaCI/CoverageBase.jl\", rev=\"master\"))"],
    ),

    # Test CoverageBase to make sure everything's on the up-and-up
    steps.ShellCommand(
        name="Test CoverageBase.jl",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", "import Pkg; Pkg.test(\"CoverageBase\")"],
        haltOnFailure=True,
    ),

    # Run Julia, gathering coverage statistics
    steps.MakeDirectory(dir=util.Interpolate("build/%(prop:juliadir)s/LCOV")),
    steps.ShellCommand(
        name="Run tests",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"),
                 "--sysimage-native-code=no", util.Interpolate("--code-coverage=%(prop:juliadir)s/LCOV/cov-%%p.info"),
                 "-e", run_coverage_cmd],
        # Fail out if 60 minutes have gone by with nothing printed to stdout
        timeout=60*60,
        # Kill everything if the overall job has taken more than 10 hours
        maxTime=60*60*10,
        # Give the process 10 seconds to print out the current backtraces when being killed
        sigtermTime=10,
    ),
    #submit the results!
    steps.ShellCommand(
        name="Gather test results and Submit",
        command=[util.Interpolate("%(prop:juliadir)s/bin/julia"), "-e", util.Interpolate(analyse_and_submit_cov_cmd)],
        env={'COVERALLS_TOKEN':COVERALLS_REPO_TOKEN, 'CODECOV_REPO_TOKEN':CODECOV_REPO_TOKEN},
        logEnviron=False,
    ),
])

# Add a nightly scheduled build for Coverage
coverage_nightly_scheduler = schedulers.Nightly(
    name="Julia Nightly Coverage Build",
    builderNames=[
        "coverage-linux64",
    ],
    hour=[5],
    change_filter=util.ChangeFilter(
        project=['JuliaLang/julia'],
        branch='master',
    ),
    properties={'download_url': "https://julialangnightlies-s3.julialang.org/bin/linux/x64/julia-latest-linux64.tar.gz"},
    onlyIfChanged=True,
)
c['schedulers'].append(coverage_nightly_scheduler)

c['schedulers'].append(schedulers.ForceScheduler(
    name="force_coverage",
    label="Force coverage build",
    builderNames=["coverage-linux64"],
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
    name="coverage-linux64",
    workernames=["tabularasa_" + x for x in builder_mapping["linux64"]],
    tags=["Coverage"],
    factory=julia_coverage_factory
))
