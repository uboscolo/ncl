#!/usr/bin/env python
import xml.etree.ElementTree as ET
import sys
import getpass
import getopt
from ncl_lib import *

def Usage():
    print "Usage: %s <xml>" % sys.argv[0]

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:", ["help", "verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        Usage()
        sys.exit(1)

    options = {}
    arglen = len(argv)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            options["verbose"] = True
            arglen -= 1
        elif o in ("-h", "--help"):
            Usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    # ...
    if arglen != 1:
        Usage()
        sys.exit(1)

    script, xml_file = sys.argv
    tree = ET.parse(xml_file)

    league_tag = tree.getroot()
    league_name = league_tag.attrib['name']
    league = League(league_name)

    for conf_tag in league_tag:
        conf_name = conf_tag.attrib['name']
        league.Add(conf_name)
        for div_tag in conf_tag:
            div_name = div_tag.attrib['name']
            current_conf = league.conferences_table_by_name[conf_name]
            current_conf.Add(div_name)
            for team_tag in div_tag:
                team_name = team_tag.attrib['name']
                team_strength = int(team_tag.attrib['strength'])
                curr_div = current_conf.divisions_table_by_name[div_name]
                curr_div.Add(team_name, team_strength)

    try:
        league.Display()
        league.Initialize()
        league.Play()
        league.Destroy()
    except IOError as err:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
