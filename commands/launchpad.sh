#!/bin/bash
set -e

# This script functions best when the following are installed:
#   wget, git, bzr, dch, make, python (with the "requests" module installed, for Travis-ci API)


# Note that in order to push to lp:~staticfloat/julianightlies/trunk, you need my GPG private key
TEAM=~staticfloat
PROJECT=julianightlies
JULIA_GIT_URL="https://github.com/JuliaLang/julia.git"
DEBIAN_GIT_URL="https://github.com/staticfloat/julia-debian.git"
JULIA_GIT_BRANCH=master
DEBIAN_GIT_BRANCH=master
BUILD_DIR=/tmp/julia-packaging/ubuntu

cd $(dirname $0)
ORIG_DIR=$(pwd)

if [[ -z "$1" ]]; then
    echo "Usage: $0 <commit sha>"
    exit 1
fi
COMMIT="$1"

# Check if we've been downloaded as a git directory.  If so, update ourselves!
if [[ -d .git ]]; then
    git pull
fi

# Store everything in a temp dir
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Get the git branch
if test ! -d julia-${JULIA_GIT_BRANCH}; then
    git clone ${JULIA_GIT_URL} julia-${JULIA_GIT_BRANCH}
    # Setup remote for launchpad
fi



# Get the debian directory
if test ! -d debian-${DEBIAN_GIT_BRANCH}; then
    git clone ${DEBIAN_GIT_URL} debian-${DEBIAN_GIT_BRANCH}
else
    cd debian-${DEBIAN_GIT_BRANCH}
    git pull
    cd ..
fi

# Go into our checkout of JULIA_GIT_URL
cd julia-${JULIA_GIT_BRANCH}
git checkout ${JULIA_GIT_BRANCH}
git fetch
git reset --hard origin/${JULIA_GIT_BRANCH}
make cleanall

# Checkout the commit we've been given
git checkout -B ${JULIA_GIT_BRANCH} ${COMMIT}

git submodule init
git submodule update

# Get dependencies
make NO_GIT=1 -C deps getall

# Let's build the documentation, so that we don't have to do so on the debian servers
make -C doc html
make -C doc latex

# We're going to compile LLVM on our own.  :(
make -C deps get-llvm
# Force downloading of LLVM 3.6.1 as well, so that ARM builds get happier
make LLVM_VER=3.6.1 -C deps get-llvm

# Work around our lack of git on buildd servers
make -C base version_git.jl.phony

# Run this again in an attempt to get the timestamps correct
make doc/_build/html

# Make it blaringly obvious to everyone that this is a git build when they start up Julia-
JULIA_VERSION=$(cat ./VERSION)
DATECOMMIT=$(git log --pretty=format:'%cd' --date=short -n 1 | tr -d '-')
echo "Syncing commit ${JULIA_VERSION}+$DATECOMMIT."

# Throw the debian directory into here
rm -rf debian
cp -r ../debian-${DEBIAN_GIT_BRANCH}/debian .

# Also, increment the current debian changelog, so we get git version tagged binaries
dch -v "${JULIA_VERSION}+$DATECOMMIT" "nightly git build"

# Add the launchpad remote, if we need to
if [[ -z "$(git remote show -n | grep launchpad)" ]]; then
    git remote add launchpad git+ssh://staticfloat@git.launchpad.net/~staticfloat/julianightlies
fi

# Force-push this up to launchpad
git add -f *
git commit -m "Manual import commit ${DATECOMMIT} from ${JULIA_GIT_URL}"
git push -f launchpad

exit 0
