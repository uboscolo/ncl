#!/usr/bin/env python

import sys
import getpass
import getopt
from myconnect import *

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvp:", 
            ["help", "verbose", "port="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        print "Usage: %s [options] <target hostname>" % sys.argv[0]
        sys.exit(2)

    options = {}
    arglen = len(argv)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            options["verbose"] = True
            arglen -= 1
        elif o in ("-h", "--help"):
            print "Usage: %s [options] <target hostname>" % sys.argv[0]
            sys.exit()
        elif o in ("-p", "--port"):
            options["port"] = a
            arglen -= 2
        else:
            assert False, "unhandled option"
    # ...

    if arglen != 1:
        print "Usage: %s [options] <target hostname>" % sys.argv[0]
        sys.exit(1)

    hostname = sys.argv[len(argv)]
    user = raw_input('Please Enter a User Name: ')
    password = getpass.getpass('Please Enter a Password: ')
    cmd_list = raw_input('Please Enter a Command  List: ')

    c = Connect(hostname, user, password, **options)
    c.Open()
    c.Run(cmd_list)
    c.Close()

if __name__ == "__main__":
    main(sys.argv[1:])
