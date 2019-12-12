from buildbot.www.hooks.github import GitHubEventHandler
from dateutil.parser import parse as dateparse
from twisted.internet import defer
from twisted.python import log


class JuliaGithubListener(GitHubEventHandler):
    def handle_create(self, payload, event):
        if 'ref_type' not in payload:
            import json
            payload = json.loads(payload['payload'][0])

        if payload['ref_type'] != 'tag':
            return [], 'git'
        
        change = {
            'author': payload['sender']['login'],
            'repository': payload['repository']['clone_url'],
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
            'repository': payload['repository']['clone_url'],
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


    # We override handle_pull_request to use merge commits instead of branch tip sha's
    # This requires a single changed line of code, highlighted below:
    @defer.inlineCallbacks
    def handle_pull_request(self, payload, event):
        changes = []
        number = payload['number']
        refname = 'refs/pull/{}/{}'.format(number, self.pullrequest_ref)
        basename = payload['pull_request']['base']['ref']
        commits = payload['pull_request']['commits']
        title = payload['pull_request']['title']
        comments = payload['pull_request']['body']
        repo_full_name = payload['repository']['full_name']
        head_sha = payload['pull_request']['head']['sha']

        log.msg('Processing GitHub PR #{}'.format(number),
                logLevel=logging.DEBUG)

        head_msg = yield self._get_commit_msg(repo_full_name, head_sha)
        if self._has_skip(head_msg):
            log.msg("GitHub PR #{}, Ignoring: "
                    "head commit message contains skip pattern".format(number))
            return ([], 'git')

        action = payload.get('action')
        if action not in ('opened', 'reopened', 'synchronize'):
            log.msg("GitHub PR #{} {}, ignoring".format(number, action))
            return (changes, 'git')

        properties = self.extractProperties(payload['pull_request'])
        properties.update({'event': event})
        properties.update({'basename': basename})

        # Prefer the merge commit sha, if we can find it
        revision = payload['pull_request']['merge_commit_sha']
        if revision is None:
            revision = payload['pull_request']['head']['sha']
        change = {
            'revision': revision,
            'when_timestamp': dateparse(payload['pull_request']['created_at']),
            'branch': refname,
            'revlink': payload['pull_request']['_links']['html']['href'],
            'repository': payload['repository']['html_url'],
            'project': payload['pull_request']['base']['repo']['full_name'],
            'category': 'pull',
            # TODO: Get author name based on login id using txgithub module
            'author': payload['sender']['login'],
            'comments': 'GitHub Pull Request #{0} ({1} commit{2})\n{3}\n{4}'.format(
                number, commits, 's' if commits != 1 else '', title, comments),
            'properties': properties,
        }

        if callable(self._codebase):
            change['codebase'] = self._codebase(payload)
        elif self._codebase is not None:
            change['codebase'] = self._codebase

        changes.append(change)

        log.msg("Received {} changes from GitHub PR #{}".format(
            len(changes), number))
        return (changes, 'git')
