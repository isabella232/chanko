#!/usr/bin/python
"""
Get package(s) and their dependencies

Arguments:
  <packages> := ( path/to/inputfile | package[=version] ) ...
                If a version isn't specified, the newest version is implied.

Options:
  -p --pretend   Displays which packages would be downloaded
  -f --force     Do not ask for confirmation before downloading
  -n --no-deps   Do not get package dependencies

"""

import sys
import getopt
from os.path import *

import help
from common import parse_inputfile, promote_depends
from chanko import Chanko

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <packages>" % sys.argv[0]

def display_uris(uris):
    for uri in uris:
        print uri.filename

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], ":fpn",
                                       ['force', 'pretend', 'no-deps'])
    except getopt.GetoptError, e:
        usage(e)

    opt_force = False
    opt_pretend = False
    opt_nodeps = False
    for opt, val in opts:
        if opt in ('-f', '--force'):
            opt_force = True
        elif opt in ('-p', '--pretend'):
            opt_pretend = True
        elif opt in ('-n', '--no-deps'):
            opt_nodeps = True

    if len(args) == 0:
        usage("bad number of arguments")

    if opt_force and opt_pretend:
        usage("conflicting options: --force, --pretend")

    packages = set()
    for arg in args:
        if exists(arg):
            packages.update(parse_inputfile(arg))
        else:
            packages.add(arg)

    chanko = Chanko()

    pkgcache = join(str(chanko.remote_cache.paths), 'pkgcache.bin')
    if not exists(pkgcache):
        chanko.remote_cache.refresh()

    toget = promote_depends(chanko.remote_cache, packages)
    if opt_pretend:
        uris = chanko.remote_cache.get(toget, opt_force, opt_pretend, opt_nodeps)
        display_uris(uris)

    elif chanko.remote_cache.get(toget, opt_force, opt_pretend, opt_nodeps):
        chanko.local_cache.refresh()
        chanko.log.update(packages)


if __name__ == "__main__":
    main()

