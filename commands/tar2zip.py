#!/usr/bin/env python

# convert .tar.gz to a .zip file
# usage `$ python -m tar2zip file.tar.gz`

import sys
import tarfile, zipfile

def tar2zip(name):
    assert name.endswith(".tar.gz")
    file = name.split(".tar.gz")[0]
    outfile = file + ".zip"
    tarf = tarfile.open(name=name, mode="r|gz")
    zipf = zipfile.ZipFile(file=outfile, mode="a", compression=zipfile.ZIP_DEFLATED)
    for m in tarf:
        if m.isreg():
            handle = tarf.extractfile(m)
            data = handle.read()
            fn = m.name
            zipf.writestr(fn, data)
    tarf.close()
    zipf.close()

if __name__ == "__main__":
    tar2zip(sys.argv[1])
