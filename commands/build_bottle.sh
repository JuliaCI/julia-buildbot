#!/bin/bash
FORMULA="$1"

if [[ -z "$FORMULA" ]]; then
    echo "Usage: $0 <formula>"
    exit -1
fi

echo "Building $FORMULA at" $(date)

# I guess we'll keep doing things in /usr/local for now
brew=$(which brew)
# Do this explicitly to escape the virtualenv sandbox.  :/
PATH=$(echo $PATH | tr ':' '\n' | grep -v sandbox | tr '\n' ':')

# Update our caches!
$brew update
#$brew pull 34303 --bottle

# Remove everything first, so we always start clean
$brew rm --force $($brew deps $FORMULA) 2>/dev/null
$brew rm --force $FORMULA 2>/dev/null

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
