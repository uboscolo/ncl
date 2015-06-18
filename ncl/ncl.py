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

    root_tag = tree.getroot()
    assert root_tag.tag == "league"
    league_name = root_tag.attrib['name']
    league = League(league_name)

    for next_tag in root_tag:
        if next_tag.tag == "conference":
            conf_name = next_tag.attrib['name']
            league.Add(conf_name)
            for div_tag in next_tag:
                assert div_tag.tag == "division"
                div_name = div_tag.attrib['name']
                current_conf = league.conferences_table_by_name[conf_name]
                current_conf.Add(div_name)
                for team_tag in div_tag:
                    assert team_tag.tag == "team"
                    team_name = team_tag.attrib['name']
                    team_strength = int(team_tag.attrib['strength'])
                    curr_div = current_conf.divisions_table_by_name[div_name]
                    curr_div.Add(team_name, team_strength)
        elif next_tag.tag == "distribution":
            dist_name = next_tag.attrib['name']
            assert (dist_name == "regular_season_game" or dist_name == "extra_time")
            league.CreateDistribution(dist_name)
            for score_tag in next_tag:
                assert score_tag.tag == "score"
                score = score_tag.attrib['value']
                iprob = float(score_tag.attrib['probability'])
                curr_dis = league.distributions_by_name[dist_name]
                curr_dis.AddScore(score, iprob)
        else:
            print "Error: unrecognized tag %s" % next_tag.tag
            sys.exit(1)

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
