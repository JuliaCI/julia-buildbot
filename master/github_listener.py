from buildbot.www.hooks.github import GitHubEventHandler
from dateutil.parser import parse as dateparse


class JuliaGithubListener(GitHubEventHandler):
    # In addition to all the other events, we parse release events as well
    # (for things like LLVM.jl, Cxx.jl, etc...)
    def handle_release(self, payload, event):
        if 'release' not in payload:
            import json
            payload = json.loads(payload['payload'][0])
        
        change = {
            'repository': payload['repository']['url'],
            'project': payload['repository']['full_name'],
            'tag_name': payload['release']['tag_name'],
            'revision': payload['release']['tag_name'],
            'when_timestamp': dateparse(payload['release']['published_at']),
            'revlink': payload['release']['url'],
        }

        # Do some magic here
        return [change], 'git'