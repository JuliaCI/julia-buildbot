from buildbot.process.results import SUCCESS

def slack_failed_build(build):
    if build['results'] == SUCCESS:
        return

    print(build)
    return {
       'text': 'Builder %s on %s failed: %s'%(build['builder']['name'], 'placeholder', build['url']),
    }

