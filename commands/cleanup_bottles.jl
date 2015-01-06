#!/usr/bin/env julia

# Homebrew has a nice way of dealing with version numbers, so let's just use that here
import Homebrew: make_version
import Base: isless, show

immutable Bottle
    name::String
    version::VersionNumber
    platform::String
    revision::Int64

    Bottle(n,v,p,r) = new(n,make_version(n,v),p, r == nothing ? 0 : int64(r))
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
    return isless(a.revision, b.revision)
end

function show(io::IO, x::Bottle)
    revision = x.revision > 0 ? "$(x.revision)." : ""
    print(io, "$(x.name)-$(x.version).$(x.platform).bottle.$(revision)tar.gz")
end


# Parse them all into (name-version, platform, revision):
function parsebottle(filename)
    # Unescape "+" because AWS is silly
    filename = replace(filename, ' ', '+')

    # This matches (name)-(version).(platform).bottle.(revision).tar.gz
    #     name: freeform
    #  version: decimal
    # platform: freeform
    # revision: integer
    bottle_regex = r"^(.*)-([0-9._]+)\.([^\.]+).bottle.(?:([0-9]+)\.)?tar.gz"
    m = match(bottle_regex, filename)
    if m == nothing
        println("Skipping $filename because we can't parse it as a bottle...")
        return
    end

    return Bottle(m.captures...)
end


# Get list of bottles
all_bottles = split(readchomp(`aws ls juliabottles --simple` |> `cut -f3-`),'\n')
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
for b in to_delete
    println("deleting juliabottles/$b")
    #run(`aws rm juliabottles/$b`)
end
