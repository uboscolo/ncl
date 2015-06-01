#!/usr/bin/env python

import sys
import getpass
import getopt
from myconnect import *

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvp:", ["help", "verbose", "port="])
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
        print "Usage: %s <host_name>" % sys.argv[0]
        sys.exit(1)

    hostname = sys.argv[len(argv)]
    jbuser = raw_input('Please Enter a User Name for the Jump Box: ')
    jbpassword = getpass.getpass('Please Enter a Password for the Jump Box: ')
    #target = raw_input('Please Enter a User Name for the Target Server: ')
    user = raw_input('Please Enter a User Name: ')
    password = getpass.getpass('Please Enter a Password: ')
    cmd_list = raw_input('Please Enter a Command  List: ')
 
    c = Connect(hostname, jbuser, jbpassword, **options)
    c.Open()
    c.password = password
    for srv in range(2,9): 
        target ="sf-r4-c2b" + str(srv)
        target_cmd = "ssh " + user + "@" + target
        c.Run(target_cmd)
        c.Run(cmd_list)
    c.Close()

if __name__ == "__main__":
    main(sys.argv[1:])
