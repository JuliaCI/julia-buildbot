###############################################################################
# Define everything needed to perform nightly homebrew builds
###############################################################################

homebrew_nightly_scheduler = Nightly(name="Julia Homebrew Build", builderNames=["homebrew_nightly_build"], hour=[0,8,16], branch="master", onlyIfChanged=True )
c['schedulers'].append(homebrew_nightly_scheduler)

homebrew_nightly_factory = BuildFactory()
homebrew_nightly_factory.useProgress = True
homebrew_nightly_factory.addSteps([
	ShellCommand(
		name="Remove Julia and deps",
		command=["brew", "rm", "-v", "--force", "julia", "openblas-julia", "arpack-julia", "suite-sparse-julia"],
		flunkOnFailure=False
	),
	ShellCommand(
		name="Tap tap",
		command=["brew", "tap", "staticfloat/julia"],
	),
	ShellCommand(
		name="Update tap",
		command=["bash", "-c", "cd /usr/local/Library/taps/staticfloat/homebrew-julia && git fetch && git reset --hard origin/master"]
	),
	ShellCommand(
		name="Update brew",
		command=["brew", "update"]
	),
	ShellCommand(
		name="Install Julia",
		command=["brew", "install", "-v", "--HEAD", "julia"],
		haltOnFailure=True
	),
	SetPropertyFromCommand(
		name="Get Julia version",
		command=["/usr/local/bin/julia", "-e", "println(Base.GIT_VERSION_INFO.commit[1:10])"],
		property="shortcommit"
	),
	ShellCommand(
		name="Report success",
		command=["curl", "-L", "-H", "Content-type: application/json", "-d", Interpolate('{"target": "Homebrew", "version": "%(prop:shortcommit)s"}'), "https://status.julialang.org/put/nightly"]
	)
])

# Add Homebrew nightly builder
c['builders'].append(BuilderConfig(
	name="homebrew_nightly_build",
	slavenames=["osx10.9-x64"],
	category="Nightlies",
	factory=homebrew_nightly_factory
))
