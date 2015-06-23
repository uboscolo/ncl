#!/usr/bin/env python

import sys
import os
import getpass
import optparse
import xml.etree.ElementTree as ET
from remote.connect.myconnect import *


class Host(object):

    def __init__(self):
        self.name = None
        self.prefix = None
        self.number = None
        self.domain = None
        self.ip = None
        self.username = None
        self.password = None
        self.connection = None

    def GetHostName(self):
        if not self.name:
            self.name = self.prefix
            if self.number:
                self.name += str(self.number)
            self.name += "." + self.domain
        return self.name


def main(argv):
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option('-v', '--verbose',
                  dest="verbose",
                  default=False,
                  help="turn on verbosity",
                  action="store_true",
                  )
    parser.add_option('-f', '--file',
                  dest="file",
                  help="read from xml file",
                  action="store",
                  )
    parser.add_option('-p', '--port',
                  dest="port",
                  type="int",
                  help="specify port number",
                  action="store",
                  )
    parser.add_option('--virsh-console',
                  dest="chew",
                  default=False,
                  help="turn on console reading",
                  action="store_true",
                  )
    opts, remainder = parser.parse_args()

    if len(remainder):
        parser.error("wrong number of arguments")
  
    options = {}
    cmd_list = []
    host_list = []
    if opts.verbose:
        options["verbose"] = opts.verbose
    if opts.port:
        options["port"] = opts.port
    if opts.file:
        xml_file = opts.file
        if not os.path.exists(xml_file) or not os.path.isfile(xml_file):
            print "invalid file %s" % xml_file
            sys.exit(1)
        tree = ET.parse(xml_file)
        root_tag = tree.getroot()
        assert root_tag.tag == "host"
        # range should be optional
        range = root_tag.attrib['range'].split("-")
        for next_tag in root_tag:
            if next_tag.tag == "user":
                username = next_tag.attrib['name']
            elif next_tag.tag == "password":
                password = next_tag.attrib['name']
            elif next_tag.tag == "command":
                cmd_list.append(next_tag.attrib['name'])
        for r in range:
            if not r.isdigit():
                print "invalid range %s, should be x-y" % range
                sys.exit(1)
            new_host = Host()
            host_list.append(new_host)
            new_host.prefix = root_tag.attrib['prefix']
            new_host.number = int(r)
            new_host.domain = root_tag.attrib['domain']
            new_host.username = username
            new_host.password = password

    else:
        #interactive
        new_host = Host()
        host_list.append(new_host)
        new_host.name = raw_input('Please Enter a Hostname: ')
        new_host.username = raw_input('Please Enter a User Name: ')
        new_host.password = getpass.getpass('Please Enter a Password: ')
        cmd_list.append(raw_input('Please Enter a Command: '))

    for host in host_list:
        hostname = host.GetHostName()
        c = Connect(hostname, host.username, host.password, **options)
        c.Open()
        if opts.chew:
            c.Chew(cmd_list[0])
        else:
            c.Run(cmd_list)
        c.Close()

if __name__ == "__main__":
    main(sys.argv[1:])
