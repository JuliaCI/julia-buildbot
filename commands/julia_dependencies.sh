#!/bin/bash

# We do this because if we run the command straight from buildbot, we're inside of a virtualenv jail
brew install -v --only-dependencies julia