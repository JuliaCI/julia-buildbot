#!/bin/bash

# We do this because if we run the command straight from buildbot, we're inside of a virtualenv jail
/usr/local/bin/brew install -v --only-dependencies julia