#!/bin/bash
FORMULA="$1"

if [[ -z "$FORMULA" ]]; then
    echo "Usage: $0 <formula>"
    exit -1
fi

echo "Building $FORMULA at" $(date)
# Remove the formula if it exists
brew rm $FORMULA 2>/dev/null

# Update our caches!
brew update

# Install dependencies first as bottles when possible
deps=$(brew deps -n $1)
for dep in $deps; do
	base=$(basename $dep)
	# Check to see if this depdency can be installed via bottle
	if [[ ! -z $(brew info $dep | grep bottled) ]]; then
		# If so, install it!
		brew install -v $dep
	else
		# Otherwise, build it with --build-bottle
		brew install -v --build-bottle $dep
	fi
done

# Then, finally, build the bottle!
brew install -v --build-bottle $FORMULA

# Bottle it!
brew bottle -vd $FORMULA