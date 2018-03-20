docker_build_factory = util.BuildFactory()
docker_build_factory.useProgress = True
docker_build_factory.addSteps([
    # First, check out julia-docker
    steps.Git(
        name="julia-docker checkout",
        repourl=util.Property('repository', default='git://github.com/staticfloat/julia-docker.git'),
        mode='incremental',
        method='clean',
        submodules=True,
        clobberOnFailure=True,
        progress=True
    ),

    # Build the image
    steps.ShellCommand(
        name="Build docker image",
        command=["make", "-C", util.Interpolate("%(prop:docker_folder)s"), util.Interpolate("build-%(prop:docker_image)s")],
        haltOnFailure=True,
    ),

    # Push the image
    steps.ShellCommand(
        name="Push docker image",
        command=["make", "-C", util.Interpolate("%(prop:docker_folder)s"), util.Interpolate("push-%(prop:docker_image)s")],
        haltOnFailure=True,
    ),

    # Cleanup old docker stuff
    steps.ShellCommand(
        name="Docker system prune",
        command=["docker", "system", "prune"],
    ),
])

# These are our default builder <--> folder/image correspondences
docker_builds = {
    'linux64': {
        'workerbase': [
            "centos6_9-x64",
            "ubuntu16_04-x64",
            "centos7_3-x64",
        ],
        'tabularasa': [
            "centos6_9-x64",
            "ubuntu16_04-x64",
            "centos7_3-x64",
        ],
    },
    'linux32': {
        'workerbase': [
            "centos6_9-x86",
            "ubuntu16_04-x86",
            "debian8_9-x86",
        ],
        'tabularasa': [
            "centos6_9-x86",
            "ubuntu16_04-x86",
            "debian8_9-x86",
        ],
    },
    'linuxaarch64': {
        'workerbase': [
            "centos7_3-aarch64",
        ], 
        'tabularasa': [
            "centos7_3-aarch64",
        ],
    },
    'linuxarmv7l': {
         'workerbase': [
            "debian7_11-armv7l",
        ],
        'tabularasa': [
            "debian7_11-armv7l",
        ],
   },
}

# Add a manual scheduler for running a docker build
docker_scheduler = schedulers.ForceScheduler(
    name="docker_build",
    label="Build docker images",
    builderNames=['docker_' + n for n in docker_builds],
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Julia"),
        )
    ],
    properties=[
        util.StringParameter(name="docker_folder", label="Folder (e.g. 'workerbase')", size=15, default=""),
        util.StringParameter(name="docker_image", label="Image name (e.g. 'centos6_9-x64')", size=15, default=""),
    ]
)
c['schedulers'].append(docker_scheduler)

# Build a builder and a scheduler for each of the mappings above
for builder in docker_builds:
    c['builders'].append(util.BuilderConfig(
        name="docker_" + builder,
        workernames=builder_mapping[builder],
        tags=["Docker"],
        collapseRequests=False,
        factory=docker_build_factory
    ))

    for folder in docker_builds[builder]:
        for image in docker_builds[builder][folder]:
            docker_scheduler = schedulers.Nightly(
                name="Docker %s/%s build"%(folder, image),
                builderNames=['docker_' + builder],
                properties={
                    'docker_folder': folder,
                    'docker_image': image,
                },
                hour=[3],
            )
            c['schedulers'].append(docker_scheduler)
