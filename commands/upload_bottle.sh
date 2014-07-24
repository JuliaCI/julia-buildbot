#!/bin/bash

set -e

if [[ "$#" != 1 ]]; then
	echo "Usage: $(basename $0) formula"
	exit 1
fi

PREFIX=$(basename $1)
if [[ -z $(ls /tmp/bottle_cache/$PREFIX*.tar.gz) ]]; then
	echo "ERROR: Cannot find any bottles for $PREFIX"
	exit 1;
fi

# Crappy check because we don't have a solution for Triggering/Dependent stuffage
if [ $(ls /tmp/bottle_cache/$PREFIX*.tar.gz | wc -l) -lt 3 ]; then
	echo "ERROR: Insufficient number of bottles, passing out" >&2
	echo $(ls /tmp/bottle_cache/$PREFIX*.tar.gz | wc -l) >&2
	exit 0;
fi

function upload()
{
	aws put "x-amz-acl: public-read" juliabottles "$1"
}


cd /tmp/bottle_cache

# First things first, upload everything!
for f in $PREFIX*.tar.gz; do
	echo "Uploading $f"
	upload "$f"
done

# Figure out if there's a revision included (only do this once, as all bottles must be the same)
basename=$(echo $PREFIX*.tar.gz | tr ' ' '\n' | head -1 | xargs basename)
revision=$(echo $basename | awk -F. 'function isnum(x){return(x==x+0)} { print isnum($((NF-2))) }')
if [[ "$revision" != "0" ]]; then
	revision=$(echo $basename | awk -F. '{print $((NF-2))}')
else
	revision=""
fi

echo
echo "Put this in your formula:"
echo
echo "  bottle do"
echo "    root_url 'https://juliabottles.s3.amazonaws.com'"
echo "    cellar :any" # Let's be optimistic, lol
if [[ ! -z "$revision" ]]; then
	echo "    revision $revision"
fi

# Now, emit each hash
for f in $PREFIX*.tar.gz; do
	REGEX='^(.*)-([0-9.]+)\.([^\.]+).bottle.(([0-9]+)\.)?tar.gz'
	platform=$(echo $f | sed -E "s/$REGEX/\3/")

	sha=$(shasum $f | cut -d" " -f1)
	echo "    sha1 '$sha' => :$platform"
done
echo "  end"

# If we've gotten this far, let's go ahead and clean up after ourselves
for f in $PREFIX*.tar.gz; do
	rm -f "$f"
done
