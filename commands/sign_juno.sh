#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
	echo "Usage: $0 <osx64 url> <win32 url> <win64 url>"
	exit 1
fi

OSX64_URL="$1"
WIN32_URL="$2"
WIN64_URL="$3"

if [[ "$(uname)" == "Darwin" ]]; then
	# First, clean everything out
	rm -rf juno*
	hdiutil detach /Volumes/Juno 2>/dev/null

	# Next, download OSX .dmg
	FILENAME=$(basename "$OSX64_URL")
	curl -L "$OSX64_URL" > $FILENAME

	# Mount it as read-write
	echo "Mounting $FILENAME..."
	hdiutil attach $FILENAME -shadow

	# Go in and sign it!
	echo "Signing Juno.app..."
	~/unlock_keychain.sh
	codesign -f -s "AFB379C0B4CBD9DB9A762797FC2AB5460A2B0DBE" --deep /Volumes/Juno/Juno.app
	if [[ $? != 0 ]]; then
		exit $?
	fi

	# Umount, create new .dmg
	echo "Unmounting /Volumes/Juno..."
	hdiutil detach /Volumes/Juno

	echo "Creating ${FILENAME%.*}-signed.dmg..."
	hdiutil convert $FILENAME -format UDZO -o ${FILENAME%.*}-signed.dmg -shadow -imagekey zlib-level=9
else
	if [[ "$(hostname)" == "win81x86" ]]; then
		WIN_URL="$WIN32_URL"
		FOLDER_NAME="windows32"
	else
		WIN_URL="$WIN64_URL"
		FOLDER_NAME="windows64"
	fi

	# First, clean everything out
	rm -rf juno* $FOLDER_NAME

	# Next, download windows .zip
	FILENAME=$(basename "$WIN_URL")
	curl -L "$WIN_URL" > $FILENAME

	# Next, unzip it into the current directory
	echo "Unzipping $FILENAME..."
	powershell -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('$FILENAME', '.'); }"

	# Go into the windows directory (we assume that always exists), sign juno.exe
	echo "Signing juno.exe..."
	~/sign.sh $FOLDER_NAME/juno.exe
	if [[ $? != 0 ]]; then
		exit $?
	fi

	# Zip it up
	echo "Zipping into ${FILENAME%.*}-signed.zip..."
	powershell -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::CreateFromDirectory('$FOLDER_NAME', '${FILENAME%.*}-signed.zip'); }"
fi
