#!/bin/bash
FORMULA="$1"

if [[ -z "$FORMULA" ]]; then
    echo "Usage: $0 <formula>"
    exit -1
fi

# Don't let Homebrew have its way with our precious precious formulae
export HOMEBREW_NO_AUTO_UPDATE=1
echo "Building $FORMULA at" $(date)

# I guess we'll keep doing things in /usr/local for now
brew=$(which brew)
# Do this explicitly to escape the virtualenv sandbox.  :/
PATH=$(echo $PATH | tr ':' '\n' | grep -v sandbox | tr '\n' ':')

# Update our caches!
(cd $(dirname $(which brew)) && git reset --hard origin/master)
$brew update

# Check out the "staging" branch while building
BUILD_BRANCH="staging"
TAP=$(dirname $(dirname $FORMULA))/homebrew-$(basename $(dirname $FORMULA))

if [[ ! -d $(dirname $(dirname $brew))/Library/Taps/$TAP ]]; then
	brew tap $(dirname $FORMULA)
	(cd $(dirname $(dirname $brew))/Library/Taps/$TAP && git remote set-branches --add origin staging)
fi

(cd $(dirname $(dirname $brew))/Library/Taps/$TAP && git reset --hard && git fetch && git checkout $BUILD_BRANCH; git reset --hard origin/$BUILD_BRANCH)

# Remove everything first, so we always start clean
$brew rm --force $($brew deps $FORMULA) 2>/dev/null
$brew rm --force $FORMULA 2>/dev/null
#$brew cleanup --cached
#rm -vf $($brew --cache)/*bottle.*tar.gz

# Install dependencies first as bottles when possible
deps=$($brew deps -n $1)
for dep in $deps; do
	# Check to see if this depdency can be installed via bottle
	if [[ ! -z $($brew info $dep | grep bottled) ]]; then
		# If so, install it!
		$brew install -v $dep
	else
		# Otherwise, build it with --build-bottle
		$brew install -v --build-bottle $dep
	fi
done

# Then, finally, build the bottle!
$brew install -v --build-bottle $FORMULA

# Bottle it!
$brew bottle -v $FORMULA

# Clean up after ourselves
$brew rm --force $($brew deps $FORMULA) 2>/dev/null
$brew rm --force $FORMULA 2>/dev/null
