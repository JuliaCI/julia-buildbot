###############################################################################
# Define everything needed to perform nightly homebrew builds
###############################################################################

homebrew_nightly_scheduler = schedulers.Nightly(name="Julia Homebrew Build", builderNames=["nightly_homebrew"], hour=[0,12], change_filter=util.ChangeFilter(project=['JuliaLang/julia','staticfloat/julia'], branch='master'), onlyIfChanged=True )
c['schedulers'].append(homebrew_nightly_scheduler)

homebrew_nightly_factory = util.BuildFactory()
homebrew_nightly_factory.useProgress = True
homebrew_nightly_factory.addSteps([
	steps.ShellCommand(
		name="Remove Julia and deps",
		command=["brew", "rm", "-v", "--force", "julia", "openblas-julia", "arpack-julia", "suite-sparse-julia"],
		flunkOnFailure=False
	),
	steps.ShellCommand(
		name="Tap tap",
		command=["brew", "tap", "staticfloat/julia"],
	),
	steps.ShellCommand(
		name="Update tap",
		command=["bash", "-c", "cd /usr/local/Homebrew/Library/taps/staticfloat/homebrew-julia && git fetch && git reset --hard origin/master"]
	),
	steps.ShellCommand(
		name="Update brew",
		command=["brew", "update"]
	),
	steps.ShellCommand(
		name="Install Julia",
		command=["brew", "install", "-v", "--HEAD", "julia"],
		haltOnFailure=True
	),
	steps.SetPropertyFromCommand(
		name="Get Julia version",
		command=["/usr/local/bin/julia", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
		property="shortcommit"
	),
	steps.MasterShellCommand(
		name="Report success",
		command=["curl", "-L", "-H", "Content-type: application/json", "-d", util.Interpolate('{"target": "Homebrew", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"]
	)
])

# Add Homebrew nightly builder
c['builders'].append(util.BuilderConfig(
	name="nightly_homebrew",
	workernames=["osx10_10-x64"],
	tags=["Nightlies"],
	factory=homebrew_nightly_factory
))
