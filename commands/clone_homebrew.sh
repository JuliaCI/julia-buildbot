#!/bin/bash

# Auto-detect which platform we're going to download as in brew
case $(sw_vers -productVersion) in
	10.10*)
		OSX_VER="yosemite"
		;;
	10.9*)
		OSX_VER="mavericks"
		;;
	10.8*)
		OSX_VER="mountain_lion"
		;;
	10.7*)
		OSX_VER="lion"
		;;
esac

# Manually hardcode in which platforms we want to mirror
PLATFORMS="mountain_lion mavericks yosemite"

# List all the bottles we have in AWS at the moment
AWS_LIST=$(aws ls juliabottles -l | awk '{ print $7 }')

# Loop over all dependencies of Julia
for DEP in $(brew deps --HEAD julia | grep -v staticfloat); do
	echo "Checking $DEP..."

	# Download this dependency, if we need to
	FETCH_OUTPUT=$(brew fetch --force-bottle $DEP)

	# Parse out interesting information from `brew fetch`
	CACHE_FILE=$(echo "$FETCH_OUTPUT" | grep -i downloaded | awk '{ print $3 }')
	CACHE_DIR=$(dirname "$CACHE_FILE")
	BASENAME=$(basename "$CACHE_FILE")
	DL_BASE=$(echo "$FETCH_OUTPUT" | grep -i downloading | awk {' print $3 }' | xargs dirname)

	# For each platform we care about, check to see if this BASENAME is uploaded, and if not, upload it!
	for NEW_PLATFORM in $PLATFORMS; do
		# Translate the original basename into a basename with the proper platform
		NAME=$(echo "$BASENAME" | sed -e "s/$OSX_VER/$NEW_PLATFORM/")

		# Check to see if this file is in AWS
		if [[ -z $(echo "$AWS_LIST" | grep "$NAME") ]]; then
			echo "$NAME is not on AWS, downloading and uploading all platforms..."
			curl -# -L $DL_BASE/$NAME -o $CACHE_DIR/$NAME

			# Now, upload it
			aws put --public --fail juliabottles/$NAME $CACHE_DIR/$NAME
		fi
	done
done