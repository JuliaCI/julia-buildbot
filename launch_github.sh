#!/bin/bash

source GITHUB_SECRET.sh 2>/dev/null

if [[ -z "$GITHUB_SECRET" ]]; then
	echo "ERROR: GITHUB_SECRET.sh either does not exist, or does not define \$GITHUB_SECRET"
	echo "This is necessary for vetting incoming github commits/pull requests!"
	exit 1
fi

# We don't worry about the buildbot secret
./github_buildbot.py -p 8000 --secret=$GITHUB_SECRET --auth=github:github.julialang42
