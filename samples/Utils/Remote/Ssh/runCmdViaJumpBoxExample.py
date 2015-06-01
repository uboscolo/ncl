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
    target = raw_input('Please Enter a User Name for the Target Server: ')
    user = raw_input('Please Enter a User Name: ')
    password = getpass.getpass('Please Enter a Password: ')
    #cmd_list = raw_input('Please Enter a Command  List: ')

    c = Connect(hostname, jbuser, jbpassword, **options)
    c.Open()
    c.password = password
    target_cmd = "ssh " + user + "@" + target
    c.Run(target_cmd)
    for ch in range(6,7):
        for srv in range(1,9):
            str_lst = "scope service-profile server " + str(ch) + "/" + str(srv) + "\n"
            for nic in range(3,5):
                str_lst = str_lst + "scope vnic eth" + str(nic) + "\n"
                for vlan in range(1001, 1014):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1065, 1078):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1129, 1142):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1193, 1206):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1257, 1282):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1513, 1541):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(1769, 1797):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(2001, 2014):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(2065, 2078):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(2129, 2142):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(2193, 2206):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(3001, 3014):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(3065, 3078):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(3129, 3142):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                for vlan in range(3193, 3206):
                    str_lst = str_lst + "create eth-if vlan" + str(vlan) + "\n"
                    str_lst += "exit\n"
                str_lst += "delete eth-if default\n"
                str_lst += "commit-buffer\n"
                str_lst += "exit\n"
            str_lst += "exit\n"
            #print "%s" % str_lst
            for line in str_lst.split("\n"):
                print "LINE: %s" % line
                c.Run(line)
    c.Close()

if __name__ == "__main__":
    main(sys.argv[1:])
