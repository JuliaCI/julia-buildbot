from buildbot.www.hooks.github import GitHubEventHandler

class JuliaGithubListener(GitHubEventHandler):
    # In addition to all the other events, we parse release events as well
    # (for things like LLVM.jl, Cxx.jl, etc...)
    def handle_release(self, payload, event):
        print "payload"
        print payload
        print "event"
        print event

        # Do some magic here
        return [], 'git'