#!/usr/bin/env julia

# Homebrew has a nice way of dealing with version numbers, so let's just use that here
import Base: isless, show

force = false
if "--force" in ARGS || "-f" in ARGS
    force = true
end

if length(ARGS) != 1
    println("Usage: cleanup_bottles.jl [--force/-f] <bucket>")
    println("  --force means don't ask before deleting")
    exit(-1)
end
bucket = ARGS[1]

immutable Bottle
    name::String
    version::String
    platform::String
    bottle_revision::Int64

    Bottle(n,v,p,r) = new(n,v,p, r == nothing ? 0 : int64(r))
end

function isless(a::Bottle, b::Bottle)
    if a.name != b.name
        return isless(a.name, b.name)
    end
    if a.platform != b.platform
        return isless(a.platform, b.platform)
    end
    if a.version != b.version
        return isless(a.version, b.version)
    end
    return isless(a.bottle_revision, b.bottle_revision)
end

function show(io::IO, x::Bottle)
    bottle_revision = x.bottle_revision > 0 ? "$(x.bottle_revision)." : ""
    print(io, "$(x.name)-$(x.version).$(x.platform).bottle.$(bottle_revision)tar.gz")
end


# Parse them all into (name-version, platform, revision):
function parsebottle(filename)
    # Unescape "+" because AWS is silly
    filename = replace(filename, ' ', '+')

    # This matches (name)-(version).(platform).bottle.(revision).tar.gz
    #            name: freeform
    #         version: freeform
    #        platform: freeform
    # bottle revision: integer
    bottle_regex = r"^(.+)-(.+)\.([^\.]+).bottle.(?:([0-9]+)\.)?tar.gz"
    m = match(bottle_regex, filename)
    if m == nothing
        println("Skipping $filename because we can't parse it as a bottle...")
        return
    end

    return Bottle(m.captures...)
end


# Get list of bottles
all_bottles = split(readchomp(`aws ls $bucket --simple` |> `cut -f3-`),'\n')
all_bottles = filter(x -> x != nothing, map(parsebottle, all_bottles))

# Bin them by name:
binned = Dict{String,Array{Bottle,1}}()
for b in all_bottles
    if !haskey(binned, b.name)
        binned[b.name] = Bottle[]
    end
    push!(binned[b.name], b)
end

# For each name, find the highest version/revision for each platform, delete all the others
to_delete = Bottle[]
to_keep = Bottle[]
for (name, bottles) in binned
    platforms = Dict{String,Array{Bottle,1}}()
    for b in bottles
        if !haskey(platforms, b.platform)
            platforms[b.platform] = Bottle[]
        end
        push!(platforms[b.platform], b)
    end

    keep_bottles = map( x -> maximum(x[2])::Bottle, platforms)

    for b in keep_bottles
        push!(to_keep, b)
    end

    for b in bottles
        if !(b in keep_bottles)
            push!(to_delete, b)
        end
    end
end


# Iterate through to_delete and, well, delete them!
if length(to_delete) > 0
    println("Found $(length(to_delete)) bottles to delete:")
    for b in to_delete
        println("$bucket/$b")
    end

    if !force
        response = nothing

        while !(response in ["y", "n"])
            print("Proceed? [y/n]: ")
            response = chomp(readline())
        end

        if response == "n"
            exit(0)
        end
    end

    for b in to_delete
        println("Deleting $bucket/$b")
        run(`aws rm $bucket/$b`)
    end
else
    println("No bottles to delete!")
end
