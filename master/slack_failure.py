from buildbot.process.results import FAILURE, EXCEPTION
import logging

log = logging.getLogger(__name__)

def slack_failed_build(build):
    # Only report failure/exception (in reality this still reports but with an illegal payload)
    if build['results'] not in (FAILURE, EXCEPTION):
        return

    log.info(build)
    return {
       'text': 'Builder %s on %s failed: %s'%(build['builder']['name'], 'placeholder', build['url']),
    }

