#!/usr/bin/env python

import sys
import getpass
import getopt
from master import *

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:", ["help", "verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        print "Usage: %s [options]" % sys.argv[0]
        sys.exit(2)

    options = {}
    arglen = len(argv)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            options["verbose"] = True
            arglen -= 1
        elif o in ("-h", "--help"):
            print "Usage: %s [options]" % sys.argv[0]
            sys.exit()
        else:
            assert False, "unhandled option"
    # ...

    if arglen != 0:
        print "Usage: %s" % sys.argv[0]
        sys.exit(1)

    for server in range(1, 2):
        options = {}
        options["prefix"] = "dice"
        options["suffix"] = "mitg-tew01.cisco.com"
        options["num_inst"] = 10
        options["num_vr"] = 2
        options["vr_offset"] = 20
        options["core_offset"] = 12
        options["addr_offset"] = 64
        options["protocol"] = "http"
        master = Master("Ramya", **options)
        master.createServers(server)
        master.createClients(server)
     
if __name__ == "__main__":
    main(sys.argv[1:])
