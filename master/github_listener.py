from buildbot.www.hooks.github import GitHubEventHandler
from dateutil.parser import parse as dateparse


class JuliaGithubListener(GitHubEventHandler):
    def handle_create(self, payload, event):
        if 'ref_type' not in payload:
            import json
            payload = json.loads(payload['payload'][0])

        if payload['ref_type'] != 'tag':
            return [], 'git'
        
        change = {
            'author': payload['sender']['login'],
            'repository': payload['repository']['url'],
            'project': payload['repository']['full_name'],
            'branch': payload['ref'],
            'comments': 'tag-creation commit',
            'category': 'tag',
        }

        # Do some magic here
        return [change], 'git'

    # In addition to all the other events, we parse release events as well
    # (for things like LLVM.jl, Cxx.jl, etc...)
    def handle_release(self, payload, event):
        if 'release' not in payload:
            import json
            payload = json.loads(payload['payload'][0])
        
        change = {
            'author': payload['release']['author']['login'],
            'repository': payload['repository']['url'],
            'project': payload['repository']['full_name'],
            'revision': payload['release']['tag_name'],
            'when_timestamp': dateparse(payload['release']['published_at']),
            'revlink': payload['release']['html_url'],
            'category': 'release',
            'comments': payload['release']['body'],
            'branch': payload['release']['tag_name'],
        }

        # Do some magic here
        return [change], 'git'
