from sys import exit
from random import *
import math
import re


class League(object):

    def __init__(self, name):
        self.name = name
        self.table = None

    def add_table(self, name):
        print "Adding table %s ..." % name
        self.table = Table(name)
 
    def display(self):
        print "League %s" % (self.name)
        self.table.display()

class Table(object):

    def __init__(self, name):
        self.name = name
        self.years = [ ]
        self.years_by_name = { }
        self.teams = [ ]
        self.teams_by_name = { }

    def add_year(self, name):
        print "Adding year %s ..." % name
        new_year = Year(name)
        self.years.append(new_year)
        self.years_by_name[name] = new_year

    def add_team(self, name, year, pos):
        print "Adding team %s ..." % name
        if name in self.teams_by_name.keys():
            print "Team %s already present" % name
            new_team = self.teams_by_name[name]
        else:
            new_team = Team(name)
            self.teams.append(new_team)
            self.teams_by_name[name] = new_team
        self.years_by_name[year].add_team(new_team, pos)
        new_team.update(year, pos)

    def display(self):
        print "  Table %s" % (self.name)
        for year in self.years:
            year.display()
        print "  Team Points %s" % (self.name)
        for team in sorted(self.teams, key=lambda team: team.points, reverse=True):
            team.display()

class Year(object):

    def __init__(self, name):
        self.name = name
        self.sorted_teams = [ ]

    def add_team(self, team, pos):
        self.sorted_teams.insert(pos - 1, team)

    def display(self):
        print "    Year %s" % (self.name)
        for team in self.sorted_teams:
            print "      Team %s, position: %s" % (team.name, team.pos_by_year[self.name])

class Team(object):

    def __init__(self, name):
        self.name = name
        self.pos_by_year = { }
        self.points = 0
        self.points_by_pos_table = { }
        self.points_by_pos_table[1] = "10"
        self.points_by_pos_table[2] = "6"
        self.points_by_pos_table[3] = "4"
        self.points_by_pos_table[4] = "3"
        self.points_by_pos_table[5] = "2"
        self.points_by_pos_table[6] = "1"

    def update(self, year, pos):
        self.pos_by_year[year] = pos
        self.points += int(self.points_by_pos_table[pos])
        print "Team: %s, points %d" % (self.name, self.points)

    def display(self):
        print "      Team %s: points %d" % (self.name, self.points)
