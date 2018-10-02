###############################################################################
#  Factory
###############################################################################

freebsdci_factory = util.BuildFactory()
freebsdci_factory.addSteps([
    steps.BSDSysInfo(),
    steps.BSDSetMakeVar(['make_jobs'], ['MAKE_JOBS_NUMBER']),

    steps.ShellCommand(
        name='cleanup stdlib',
        command=['rm', '-rvf', 'stdlib']
    ),

    steps.GitHub(
        repourl='git://github.com/JuliaLang/julia.git',
        mode='full',
        method='clean'),

    steps.ShellCommand(
        name='cleanall',
        command=['gmake', 'cleanall'],
    ),

    steps.ShellCommand(
        name='cleanup',
        command=['./.freebsdci.sh', 'cleanup']
    ),

    steps.Compile(
        command=['./.freebsdci.sh', 'compile'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
    ),

    steps.ShellCommand(
        name='build-stats',
        command=['./.freebsdci.sh', 'build-state'],
    ),

    steps.Test(
        command=['./.freebsdci.sh', 'runtests'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
        timeout=1200,  # 20 min
    ),

    steps.ShellCommand(
        name='test embedding',
        command=['./.freebsdci.sh', 'test-embedding'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
    ),
])

freebsdci_test_factory = util.BuildFactory()
freebsdci_test_factory.addSteps([
    steps.BSDSysInfo(),
    steps.BSDSetMakeVar(['make_jobs'], ['MAKE_JOBS_NUMBER']),

    steps.ShellCommand(
        name='cleanup stdlib',
        command=['rm', '-rvf', 'stdlib'],
    ),

    steps.ShellCommand(
        name='testing var',
        command=['/bin/sh', '-c' , 'echo $CHANGES'],
        env={
            'CHANGES': util.Property('branch'),
            'MYVAR': 'foo',
            'WORKERNAME': util.Property('workername'),
        }
    ),

    steps.GitHub(
        repourl='git://github.com/JuliaLang/julia.git',
        mode='full',
        method='clean'),

    steps.ShellCommand(
        name='cleanall',
        command=['gmake', 'cleanall'],
    ),

    steps.ShellCommand(
        name='cleanup',
        command=['./.freebsdci.sh', 'cleanup']
    ),

    steps.Compile(
        command=['./.freebsdci.sh', 'compile'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
    ),

    steps.ShellCommand(
        name='build-stats',
        command=['./.freebsdci.sh', 'build-state'],
    ),

    steps.Test(
        command=['./.freebsdci.sh', 'runtests'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
        timeout=1200,  # 20 min
    ),

    steps.ShellCommand(
        name='test embedding',
        command=['./.freebsdci.sh', 'test-embedding'],
        env={
            'WORKERNAME': util.Property('workername'),
            'MAKE_JOBS_NUMBER': util.Property('make_jobs'),
        },
    ),
])

###############################################################################
#  Builders
###############################################################################

freebsdci_builder_names = {
    'main': 'freebsdci',
    'test': 'freebsdci_test',
}

freebsdci_builders = [
    util.BuilderConfig(
        name=freebsdci_builder_names['main'],
        workernames=freebsdci_names['main'],
        tags=['freebsdci'],
        factory=freebsdci_factory),

    util.BuilderConfig(
        name=freebsdci_builder_names['test'],
        workernames=freebsdci_names['test'],
        tags=['freebsdci-test'],
        factory=freebsdci_test_factory),
]

###############################################################################
#  Schedulers
###############################################################################

freebsdci_schedulers = [
    schedulers.SingleBranchScheduler(
        name="freebsdci_master",
        change_filter=util.ChangeFilter(branch='master'),
        treeStableTimer=60,
        builderNames=[freebsdci_builder_names['main']]),

    schedulers.ForceScheduler(
        name="freebsdci_force",
        builderNames=[freebsdci_builder_names['main']]),

    schedulers.ForceScheduler(
        name="freebsdci_force_test",
        builderNames=[freebsdci_builder_names['test']]),

    schedulers.SingleBranchScheduler(
        name='freebsdci_pull_request',
        change_filter=util.ChangeFilter(
            branch_re='^refs/pull/.*',
            repository_re='https://github.com/[\w]+/julia'),
        builderNames=[freebsdci_builder_names['main']],
        treeStableTimer=10,
    ),
]

###############################################################################
#  GitHub Status Reporter
###############################################################################

freebsdci_report = reporters.GitHubStatusPush(
    token=FREEBSDCI_OAUTH_TOKEN,
    context='julia freebsd ci',
    startDescription='Build started',
    builders=[freebsdci_builder_names['main']],
    endDescription='Build done')

###############################################################################
#  GitHub Change Hook
###############################################################################

freebsdci_gh_setting = {
    'skips': [
        r'\[ *skip *ci *\]',
        r'\[ *ci *skip *\]',
    ],
    'github_property_whitelist': ['base'],
}

###############################################################################
#  Master Config
###############################################################################

c['services'].append(freebsdci_report)
c['builders'].extend(freebsdci_builders)
c['schedulers'].extend(freebsdci_schedulers)
c['www']['change_hook_dialects']['github'].update(freebsdci_gh_setting)
