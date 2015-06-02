#!/usr/bin/env python
import xml.etree.ElementTree as ET
from ncl_lib import *
from sys import argv

if len(argv) != 2:
    print "Usage: ncl.py xml_file"
    exit(1)

script, xml_file = argv

#tree = ET.parse('ncl.xml')
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

league.Display()

league.Initialize()

league.Play()
