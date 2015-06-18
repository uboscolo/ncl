#!/usr/bin/env python
import xml.etree.ElementTree as ET
from league_lib import *
from sys import argv

if len(argv) != 2:
    print "Usage: ncl.py xml_file"
    exit(1)

script, xml_file = argv

tree = ET.parse(xml_file)

league_tag = tree.getroot()
league_name = league_tag.attrib['name']
league = League(league_name)

for tab_tag in league_tag:
    tab_name = tab_tag.attrib['name']
    league.add_table(tab_name)
    for year_tag in tab_tag:
        year_name = year_tag.attrib['name']
        league.table.add_year(year_name)
        for team_tag in year_tag:
            team_name = team_tag.attrib['name']
            team_pos = int(team_tag.attrib['position'])
            league.table.add_team(team_name, year_name, team_pos)

league.display()
