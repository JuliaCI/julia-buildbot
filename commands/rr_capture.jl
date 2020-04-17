using Pkg

if length(ARGS) < 3
    println(stderr, "Usage: rr_capture.jl [buildnumber] [shortcommit] [command...]")
    exit(2)
end

const TIMEOUT = 2*60*60 # seconds

run_id = popfirst!(ARGS)
shortcommit = popfirst!(ARGS)

new_env = copy(ENV)
mktempdir() do dir
    Pkg.activate(dir)
    Pkg.add("rr_jll")

    using rr_jll
    rr() do rr_path
        new_env = copy(ENV)
        new_env["_RR_TRACE_DIR"] = joinpath(dir, "rr_traces")
        new_env["JULIA_TEST_EXENAME"] = "$(rr_path) record --nested=detach julia"
        t_start = time()
        proc = run(setenv(`rr record $ARGS`, new_env), (stdin, stdout, stderr); wait=false)

        # Wait until either we timeout, or the process finishes
        while (time() < t_start + TIMEOUT) && isopen(proc)
            sleep(0.5)
        end

        if isopen(proc)
            println(stderr, "\n\nProcess timed out. Signalling `rr` for force-cleanup!")
            kill(proc, Base.SIGTERM)
            
            @async begin
                # Give `rr` one minute to clean things up
                sleep(60)
                if isopen(proc)
                    println(stderr, "\n\n`rr` failed to cleanup within one minute, killing!")
                    exit(1)
                end
            end
        end

        # If we got `rr` to finish properly, let's look at the exit code
        wait(proc)

        # On a non-zero exit code, upload the `rr` trace
        if proc.exitcode != 0
            println(stderr, "`rr` returned $(proc.exitcode), packing and uploading traces...")

            # Pack all traces
            trace_dirs = [joinpath(dir, "rr_traces", f) for f in readdir(joinpath(dir, "rr_traces"))]
            filter!(isdir, trace_dirs)
            for trace_dir in trace_dirs
                println(stderr, " -> packing $(basename(trace_dir))")
                run(`$(rr_path) pack $(trace_dir)`)
            end

            # Tar it up
            mkpath("dumps")
            datestr = Dates.format(now(), dateformat"yyyy-mm-dd_HH_MM_SS") 
            Pkg.PlatformEngines.package(dir, "dumps/rr-run$(run_id)-gitsha$(shortcommit)-$(datestr).tar.gz")
        end
    end
end
