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
BZR_BRANCH=trunk
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
fi

# Get the bzr branch
if test ! -d ${BZR_BRANCH}; then
    bzr branch http://bazaar.launchpad.net/${TEAM}/${PROJECT}/${BZR_BRANCH}/
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

# Checkout the commit we've been given
git checkout -B ${JULIA_GIT_BRANCH} ${COMMIT}

git submodule init
git submodule update

# Hack to get around our lack of packaging of dsfmt and libgit2
make -C deps get-dsfmt get-libgit2

# Let's build the documentation, so that we don't have to do so on the debian servers
make -C doc html
make -C doc latex
make -C doc helpdb.jl

# We're going to compile LLVM on our own.  :(
make -C deps get-llvm

# Work around our lack of git on buildd servers
make -C base version_git.jl.phony

# Make it blaringly obvious to everyone that this is a git build when they start up Julia-
JULIA_VERSION=$(cat ./VERSION)
DATECOMMIT=$(git log --pretty=format:'%cd' --date=short -n 1 | tr -d '-')
echo "Syncing commit ${JULIA_VERSION}+$DATECOMMIT."
cd ..

# Now go into the bzr branch and copy everything over
cd ${BZR_BRANCH}
bzr pull http://bazaar.launchpad.net/${TEAM}/${PROJECT}/${BZR_BRANCH}/
rm -rf *
cp -r ../julia-${JULIA_GIT_BRANCH}/* .

# Throw the debian directory into here as well, instead of relying on launchpad
cp -r ../debian-${DEBIAN_GIT_BRANCH}/debian .

# Also, increment the current debian changelog, so we get git version tagged binaries
dch -v "${JULIA_VERSION}+$DATECOMMIT" "nightly git build"

bzr add
bzr ci -m "Manual import commit ${DATECOMMIT} from ${JULIA_GIT_URL}/${JULIA_GIT_BRANCH}" || true
bzr push lp:${TEAM}/${PROJECT}/${BZR_BRANCH}
cd ..

exit 0
