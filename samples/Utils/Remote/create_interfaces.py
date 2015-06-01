#!/usr/bin/env python

import sys
import getpass
import getopt
from interfaces import *

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:", ["help", "verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        print "Usage: %s [options] <machine list>" % sys.argv[0]
        sys.exit(2)

    options = {}
    arglen = len(argv)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            options["verbose"] = True
            arglen -= 1
        elif o in ("-h", "--help"):
            print "Usage: %s [options] <machine list>" % sys.argv[0]
            sys.exit()
        else:
            assert False, "unhandled option"
    # ...

    if arglen != 1:
        print "Usage: %s <machine list>" % sys.argv[0]
        sys.exit(1)

    mlist = sys.argv[len(argv)]
    
    for server in range(1,5):
        hostname = "sf-r5-c2b" + str(server) + ".mitg-tew01.cisco.com"
        serv_num = server + 16
        options = {}
        options["vlan_offset"] = 64
        interfaces = Interfaces(**options)
        interfaces.Create(serv_num, 4, ["eth2", "eth3", "eth4", "eth5"])
        #interfaces.Transfer(hostname, "root", "starent", "/etc/network/interfaces.new")
        interfaces.Display(hostname, "root", "starent", "/etc/network/interfaces.new")


if __name__ == "__main__":
    sys.path.append("Ssh")
    from myconnect import *
    main(sys.argv[1:])
