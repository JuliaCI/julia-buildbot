## A note on unneecssary complexity
# We have gone through a few different standards on naming Julia's build artifacts.
# The latest, as of this writing, is the `sf/consistent_distnames` branch on github,
# and simplifies things relative to earlier versions.  However, this buildbot needs
# to be able to build/upload Julia versions of all reasonably recent versions.
# `sf/consistent_distnames` should be merged before the 0.6 release, which means
# that once the release _after_ 0.6 is out in the wild and 0.5 is put to rest,
# we can safely remove anything that talks about non-`sf/consistent_distnames`
# compatibility/workarounds.


# Helper function to generate the necessary julia invocation to get metadata
# about this build such as major/minor versions
@util.renderer
def make_julia_version_command(props_obj):
    command = [
        "usr/bin/julia",
        "-e",
        "println(\"$(VERSION.major).$(VERSION.minor).$(VERSION.patch)\\n$(Base.GIT_VERSION_INFO.commit[1:10])\")"
    ]

    if is_windows(props_obj):
        command[0] += '.exe'
    return command

# Parse out the full julia version generated by make_julia_version_command's command
def parse_julia_version(return_code, stdout, stderr):
    lines = stdout.split('\n')
    return {
        "majmin": lines[0][:lines[0].rfind('.')],
        "version": lines[0].strip(),
        "shortcommit": lines[1].strip(),
    }

def parse_git_log(return_code, stdout, stderr):
    lines = stdout.split('\n')
    return {
        "commitmessage": lines[0],
        "commitname": lines[1],
        "commitemail": lines[2],
        "authorname": lines[3],
        "authoremail": lines[4],
    }

def gen_local_filename(props_obj):
    props = props_obj_to_dict(props_obj)

    # Get the output of the `make print-JULIA_BINARYDIST_FILENAME` step
    artifact = "{artifact_filename}".format(**props).strip()

    # First, see if we got a JULIA_BINARYDIST_FILENAME output
    if artifact[:26] == "JULIA_BINARYDIST_FILENAME=" and len(artifact) > 26:
        return artifact[26:] + ".{os_pkg_ext}".format(**props)
    else:
        # If not, use non-sf/consistent_distnames naming
        if is_mac(props_obj):
            return "contrib/mac/app/Julia-{version}-{shortcommit}.{os_pkg_ext}".format(**props)
        elif is_windows(props_obj):
            return "julia-{version}-{tar_arch}.{os_pkg_ext}".format(**props)
        else:
            # We made bad decisions in the past
            if props['tar_arch'] == "armv7l":
                return "julia-{shortcommit}-Linux-arm.{os_pkg_ext}".format(**props)
            return "julia-{shortcommit}-Linux-{tar_arch}.{os_pkg_ext}".format(**props)


def gen_upload_filename(props_obj):
    props = props_obj_to_dict(props_obj)
    # We don't like "winnt" at the end of files, we use just "win" instead.
    props["os_name_file"] = props["os_name"]
    if props["os_name_file"] == "winnt":
        props["os_name_file"] = "win"
    return "julia-{shortcommit}-{os_name_file}{bits}.{os_pkg_ext}".format(**props)

def gen_upload_path(props_obj, namespace=None):
    up_arch = props_obj.getProperty("up_arch")
    majmin = props_obj.getProperty("majmin")
    upload_filename = props_obj.getProperty("upload_filename")
    os = get_os_name(props_obj)
    if namespace is None:
        return "julialangnightlies/bin/%s/%s/%s/%s"%(os, up_arch, majmin, upload_filename)
    else:
        return "julialangnightlies/%s/bin/%s/%s/%s/%s"%(namespace, os, up_arch, majmin, upload_filename)

def gen_latest_upload_path(props_obj, namespace=None):
    up_arch = props_obj.getProperty("up_arch")
    upload_filename = props_obj.getProperty("upload_filename")
    if upload_filename[:6] == "julia-":
        split_name = upload_filename.split("-")
        upload_filename = "julia-latest-%s"%(split_name[2])
    os = get_os_name(props_obj)
    if namespace is None:
        return "julialangnightlies/bin/%s/%s/%s"%(os, up_arch, upload_filename)
    else:
        return "julialangnightlies/%s/bin/%s/%s/%s"%(namespace, os, up_arch, upload_filename)



def gen_download_url(props_obj, namespace=None):
    base = 'https://s3.amazonaws.com'
    return '%s/%s'%(base, gen_upload_path(props_obj, namespace=namespace))

def gen_latest_download_url(props_obj):
    base = 'https://s3.amazonaws.com'
    return '%s/%s'%(base, gen_latest_upload_path(props_obj))



# This is a weird buildbot hack where we really want to parse the output of our
# make command, but we also need access to our properties, which we can't get
# from within an `extract_fn`.  So we save the output from a previous
# SetPropertyFromCommand invocation, then invoke a new command through this
# @util.renderer nonsense.  This function is supposed to return a new command
# to be executed, but it has full access to all our properties, so we do all our
# artifact filename parsing/munging here, then return ["true"] as the step
# to be executed.
@util.renderer
def munge_artifact_filename(props_obj):
    # Generate our local and upload filenames
    local_filename = gen_local_filename(props_obj)
    upload_filename = gen_upload_filename(props_obj)

    props_obj.setProperty("local_filename", local_filename, "munge_artifact_filename")
    props_obj.setProperty("upload_filename", upload_filename, "munge_artifact_filename")
    return ["true"]

@util.renderer
def render_upload_command(props_obj):
    upload_path = gen_upload_path(props_obj, namespace="pretesting")
    upload_filename = props_obj.getProperty("upload_filename")
    return ["/bin/bash", "-c", "~/bin/try_thrice ~/bin/aws put --fail --public %s /tmp/julia_package/%s"%(upload_path, upload_filename)]

@util.renderer
def render_promotion_command(props_obj):
    src_path = gen_upload_path(props_obj, namespace="pretesting")
    dst_path = gen_upload_path(props_obj)
    return ["/bin/bash", "-c", "~/bin/try_thrice ~/bin/aws cp --fail --public %s /%s"%(dst_path, src_path)]

@util.renderer
def render_latest_promotion_command(props_obj):
    src_path = gen_upload_path(props_obj, namespace="pretesting")
    dst_path = gen_latest_upload_path(props_obj)
    return ["/bin/bash", "-c", "~/bin/try_thrice ~/bin/aws cp --fail --public %s /%s"%(dst_path, src_path)]

@util.renderer
def render_cleanup_pretesting_command(props_obj):
    del_path = gen_upload_path(props_obj, namespace="pretesting")
    return ["/bin/bash", "-c", "~/bin/try_thrice ~/bin/aws rm %s"%(del_path)]

@util.renderer
def render_download_url(props_obj):
    return gen_download_url(props_obj)

@util.renderer
def render_pretesting_download_url(props_obj):
    return gen_download_url(props_obj, namespace="pretesting")

@util.renderer
def render_make_app(props_obj):
    props = props_obj_to_dict(props_obj)

    new_way = "make {flags} app".format(**props)
    old_way = "make {flags} -C contrib/mac/app && mv contrib/mac/app/*.dmg {local_filename}".format(**props)

    # We emit a bash command that attempts to run `make app` (which is the nice
    # `sf/consistent_distnames` shortcut), and if that fails, it runs the steps
    # manually, which boil down to `make -C contrib/mac/app` and moving the
    # result to the top-level, where we can find it.  We can remove this once
    # 0.6 is no longer being built.
    return [
        "/bin/bash",
        "-c",
        "~/unlock_keychain.sh && (%s || (%s))"%(new_way, old_way)
    ]

def build_download_julia_cmd(props_obj):
    download_url = props_obj.getProperty("download_url")

    # Build commands to download/install julia
    if is_mac(props_obj):
        # Download the .dmg
        cmd  = "curl -L '%s' -o julia-installer.dmg && "%(download_url)
        # Mount it
        cmd += "hdiutil mount julia-installer.dmg && "
        # copy its `julia` folder contents here.
        cmd += "cp -Ra /Volumes/Julia-*/Julia-*.app/Contents/Resources/julia/* . && "
        # Unmount any and all Julia disk images
        cmd += "for j in /Volumes/Julia-*; do hdiutil unmount \"$j\"; done && "
        # Delete the .dmg
        cmd += "rm -f julia-installer.dmg"
    elif is_windows(props_obj):
        # Download the .exe
        cmd = "curl -L '%s' -o julia-installer.exe && "%(download_url)
        # Make it executable
        cmd += "chmod +x julia-installer.exe && "
        # Extract it into the current directory
        cmd += "./julia-installer.exe /S /D=$(cygpath -w $(pwd)) && "
        # Remove the .exe
        cmd += "rm -f julia-installer.exe"
    else:
        # Oh linux.  Your simplicity always gets me
        cmd = "curl -L '%s' | tar --strip-components=1 -zx"%(download_url)
    return ["/bin/bash", "-c", cmd]


@util.renderer
def download_julia(props_obj, namespace=None):
    # If we already have an "url", use that, otherwise try to generate it:
    if not props_obj.hasProperty('download_url'):
        # Calculate upload_filename, add to properties, then get download url
        upload_filename = gen_upload_filename(props_obj)
        props_obj.setProperty("upload_filename", upload_filename, "download_julia")
        download_url = gen_download_url(props_obj)
        props_obj.setProperty("download_url", download_url, "download_julia")
    return build_download_julia_cmd(props_obj)

def download_latest_julia(props_obj):
    # Fake `gen_upload_filename()` into giving us something like
    # `julia-latest-linux64.tar.gz` instead of a true shortcommit
    props_obj.setProperty("shortcommit", "latest", "download_latest_julia")
    upload_filename = gen_upload_filename(props_obj)
    props_obj.setProperty("upload_filename", upload_filename, "download_latest_julia")

    download_url = gen_latest_download_url(props_obj)
    props_obj.setProperty("download_url", download_url, "download_latest_julia")
    return build_download_julia_cmd(props_obj)

@util.renderer
def render_tester_name(props_obj):
    props = props_obj_to_dict(props_obj)
    return "Julia %s Testing"%(props['buildername'].replace('package_', ''))
