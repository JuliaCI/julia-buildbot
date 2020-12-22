from buildbot.process.results import FAILURE, EXCEPTION

def slack_failed_build(build):
    # Only report failure/exception (in reality this still reports but with an illegal payload)
    if build['results'] not in (FAILURE, EXCEPTION):
        return

    # Only report if we have a URL:
    if 'url' not in build:
        return
    url = build['url']

    # Try to get the buildername:
    builder_name = '<unknown builder>'
    if 'builder' in build and 'name' in build['builder']:
        builder_name = build['builder']['name']

    # Try to get the worker name:
    worker_name = '<unknown worker>'
    if 'properties' in build and 'workername' in build['properties']:
        worker_name = build['properties']['workername'][0]

    return {
       'text': 'Builder %s on %s failed: %s'%(builder_name, worker_name, url),
    }

