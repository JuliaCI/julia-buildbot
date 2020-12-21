from buildbot.process.results import FAILURE

def slack_failed_build(build):
    if build['results'] != FAILURE:
        return

    return {
       'text': 'Builder %s on %s failed: %s'%(build['builder']['name'], build['worker']['name'], build['url']),
    }

