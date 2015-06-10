from sys import exit
from random import *
import math
import re

class DistributionTables(object):
    """These Tables are used to simulate results and
       scores"""

    def __init__(self, name):
        self.name = name
        self.score_distr = {}
        self.result_distr = Distribution()

    def Initialize(self):
        self.score_distr["away"] = Distribution()
        self.score_distr["draw"] = Distribution()
        self.score_distr["home"] = Distribution()
        # 0
        self.score_distr["draw"].Add("0-0", 0.085)
        # 1
        self.score_distr["home"].Add("1-0", 0.125)
        self.score_distr["away"].Add("0-1", 0.065)
        # 2
        self.score_distr["draw"].Add("1-1", 0.120)
        self.score_distr["home"].Add("2-0", 0.090)
        self.score_distr["away"].Add("0-2", 0.050)
        # 3
        self.score_distr["home"].Add("2-1", 0.093)
        self.score_distr["away"].Add("1-2", 0.053)
        self.score_distr["home"].Add("3-0", 0.045)
        self.score_distr["away"].Add("0-3", 0.015)
        # 4
        self.score_distr["draw"].Add("2-2", 0.045)
        self.score_distr["home"].Add("4-0", 0.025)
        self.score_distr["away"].Add("0-4", 0.015)
        self.score_distr["home"].Add("3-1", 0.045)
        self.score_distr["away"].Add("1-3", 0.025)
        # 5
        self.score_distr["home"].Add("3-2", 0.020)
        self.score_distr["away"].Add("2-3", 0.015)
        self.score_distr["home"].Add("4-1", 0.015)
        self.score_distr["away"].Add("1-4", 0.010)
        self.score_distr["home"].Add("5-0", 0.005)
        self.score_distr["away"].Add("0-5", 0.003)
        # 6
        self.score_distr["draw"].Add("3-3", 0.007)
        self.score_distr["home"].Add("4-2", 0.007)
        self.score_distr["away"].Add("2-4", 0.002)
        self.score_distr["home"].Add("5-1", 0.005)
        self.score_distr["away"].Add("1-5", 0.002)
        self.score_distr["home"].Add("6-0", 0.002)
        self.score_distr["away"].Add("0-6", 0.001)
        # 7
        self.score_distr["home"].Add("4-3", 0.003)
        self.score_distr["away"].Add("3-4", 0.002)
        self.score_distr["home"].Add("5-2", 0.001)
        self.score_distr["away"].Add("2-5", 0.001)
        self.score_distr["home"].Add("6-1", 0.001)
        self.score_distr["away"].Add("1-6", 0.001)
        self.score_distr["home"].Add("7-0", 0.001)
        # results
        self.result_distr.Add("away", 0.32)
        self.result_distr.Add("draw", 0.19)
        self.result_distr.Add("home", 0.49)

 
class League(object):

    def __init__(self, name):
        self.name = name
        self.tables = DistributionTables("Tables")
        self.conferences = [ ]
        self.conferences_table_by_name = { } 
        self.playoff_teams = [ ]
        self.champion = None
        self.schedule = None

    def __Final(self):
        team1 = self.conferences[0].champion
        team2 = self.conferences[1].champion
        final = Match(team1, team2, self.tables)
        print "\n League %s Final\n" % self.name
        final.PlayWinner()
        print "\nThe League Champion is %s!\n" % (final.winner.name)

    def Add(self, name):
        print "Adding conference %s ..." % name
        new_conf = Conference(name)
        self.conferences.append(new_conf)
        self.conferences_table_by_name[name] = new_conf
        
    def Display(self):
        print "\n"
        print "League %s has %d conferences:" % (
            self.name, len(self.conferences))
        for conf in self.conferences:
            print "\t - Conference %s" % (conf.name)
        for conf in self.conferences:
            conf.Display()

    def Initialize(self):
        self.tables.Initialize()
        for conf in self.conferences:
            conf.Initialize(self.tables)
        
    def Play(self):
        # Play Regular Season
        # needs enhancement
        play_on = True
        while play_on:
            for conf in self.conferences:
                conf.PlayDiv()
                play_on = play_on and not conf.schedule.completed
        # Display Regular Season Results and Setup Playoffs
        for conf in self.conferences:
            conf.schedule.completed = False
            for div in conf.divisions:
                div.schedule.stats.Display(div.name)
            conf.SetupPlayoffs()
        # Play Conference Playoffs
        print "\n Conference Playoffs start..."
        play_on = True
        while play_on:
            for conf in self.conferences:
                conf.BuildPlayoffs()
                conf.Play()
                play_on = play_on and not conf.schedule.completed
        # Play Final
        self.__Final()

    def Sort(self, teams):
        sorted_teams = [ ]
        for team in teams:
            if len(sorted_teams) > 0:
                found = 0
                for pos in range(len(sorted_teams)):
                    if team.points >= sorted_teams[pos].points:
                        sorted_teams.insert(pos, team)
                        found = 1
                        break
                if found == 0: 
                    sorted_teams.append(team)
            else:
                sorted_teams.append(team)
        return sorted_teams



class Conference(League):

    def __init__(self, name):
        super(Conference, self).__init__(name)
        self.divisions = [ ]
        self.divisions_table_by_name = { }
        self.series_len = 3
        self.series_list = [ ]

    def Add(self, name):
        print "Adding division %s ..." % name
        new_div = Division(name)
        self.divisions.append(new_div) 
        self.divisions_table_by_name[name] = new_div

    def BuildPlayoffs(self):
        if len(self.series_list) > 0:
            return
        for i in range(0, len(self.playoff_teams)/2):
            team1 = self.playoff_teams[i]
            team2 = self.playoff_teams[len(self.playoff_teams) - 1 - i]
            new_series = Series(team1, team2, self.series_len)
            self.series_list.append(new_series)
        for i in range(1, self.series_len + 1):
            new_day = Day(i)
            self.schedule.days.append(new_day)
            for s in self.series_list:
                if (i - 1) % 2:
                    match = Match(s.team2, s.team1, self.tables)
                else:
                    match = Match(s.team1, s.team2, self.tables)
                match.series = s
                new_day.Add(match)
        self.schedule.SetCurrentDay(0)

    def Display(self):
        print "Conference %s has %d divisions:" % (
            self.name, len(self.divisions))
        for div in self.divisions:
            print "\t - Division %s" % (div.name)
        for div in self.divisions:
            div.Display()

    def Initialize(self, tables):
        self.tables = tables
        for div in self.divisions:
            div.Initialize(self.tables)
            div.schedule.Display(div.name)
        self.schedule = Schedule(tables)

    def Play(self):
        self.schedule.Play(0)
        if self.schedule.completed:
            for s in self.series_list:
                loser = self.playoff_teams.index(s.loser)
                self.playoff_teams.pop(loser)
            if len(self.playoff_teams) > 1:
                self.schedule.completed = False
                self.schedule.days = [ ]
                self.series_list = [ ]
            else:
                self.champion = self.playoff_teams[0]
                print "Conference %s - Playoffs are over" % self.name
                print "Winner: %s\n" % self.champion.name

    def PlayDiv(self):
        play_on = True
        for div in self.divisions:
            # Regular Season
            div.Play()
            play_on = play_on and not div.schedule.completed
        self.schedule.completed = not play_on

    def SetupPlayoffs(self):
        # Build Conference Playoff team list
        for div in self.divisions:
            self.playoff_teams += div.playoff_teams
        self.playoff_teams = self.Sort(self.playoff_teams)


class Division(Conference):

    def __init__(self, name):
        super(Division, self).__init__(name)
        self.teams = [ ]
        self.table = Table()

    def Add(self, name, strength):
        print "Adding team %s with strength: %d ..." % (name, strength)
        new_team = Team(name, strength)
        self.teams.append(new_team) 

    def Display(self):
        print "Division %s has %d teams:" % (self.name, len(self.teams))
        for div in self.teams:
           print "\t - Team %s" % (div.name)

    def Initialize(self, tables):
        self.tables = tables
        self.schedule = Schedule(tables)
        self.schedule.RoundRobin(self.teams)
        self.schedule.SwapHomeAway()
        self.schedule.SetCurrentDay(0)

    def Play(self):
        self.schedule.Play(90)
        self.table.Sort(self.teams)
        self.table.Display(self.name)
        if self.schedule.completed:
            # Build Playoffs
            print "\n Division %s - Regular Season is over\n" % self.name
            teams = self.table.sorted_teams
            self.playoff_teams = teams[0:len(teams)/2]
            for team in self.playoff_teams:
                print "Team %s made the playoffs" % team.name
            print ""


class Table(object):

    def __init__(self):
        self.sorted_teams = [ ]

    def Sort(self, teams):
        sorted_teams = [ ]
        for team in teams:
            if len(sorted_teams) > 0:
                found = 0
                for pos in range(len(sorted_teams)):
                    if team.points >= sorted_teams[pos].points:
                        sorted_teams.insert(pos, team)
                        found = 1
                        break
                if found == 0: 
                    sorted_teams.append(team)
            else:
                sorted_teams.append(team)
        self.sorted_teams = sorted_teams[:]

    def Display(self, name):
        print "Table\n"
        print "--- {:15s} ---".format(name) 
        for team in self.sorted_teams:
            print "{:20s} {:2d}".format(team.name, team.points)
        print ""


class Team(object):

    def __init__(self, name, strength):
        self.name = name
        self.strength = strength
        self.points = 0
        self.series_wins = 0


class Statistics(object):

    def __init__(self, name):
        self.name = name
        self.table = { }

    def Add(self, tag):
        self.table[tag] = 0
        
    def Update(self, tag, value):
        self.table[tag] += value

    def Display(self, div_name):
        print "----------- Division %s Statistics: -----------" % div_name
        total = 0
        for t in self.table.keys():
            total += self.table[t]
        for t in self.table.keys():
            print "{:20s} {:2.2f}".format(t, float(self.table[t])/total*100)
            #print "%s victory rate: %f" % (t, float(self.table[t])/total*100)


class Schedule(object):

    def __init__(self, tables):
        self.rotating_table = { }
        self.days = [ ]
        self.current_day = None
        self.completed = False
        self.tables = tables
        self.stats = Statistics("Statistics")
        self.stats.Add("home")
        self.stats.Add("away")
        self.stats.Add("draw")
 
    def Display(self, div_name):
        print "----------- Division %s Schedule: -----------" % div_name
        for day in self.days:
            for match in day.matches:
                home = match.home_team.name
                away = match.away_team.name
                print "Day %s - Match: %s vs %s" % (day.number, home, away) 

    def SetCurrentDay(self, index):
        self.current_day = self.days[index]

    def Play(self, minutes):
        if self.current_day.number <= len(self.days):
            print "Day: %d\n" % (self.current_day.number)
            for match in self.current_day.matches:
                if minutes > 0:
                    print "Starting %s-minute game ..." % (minutes)
                    match.Play(minutes)
                    match.Update()
                    self.stats.Update(match.result.result, 1)
                    print "Game over ...\n"
                else:
                    if not match.series.is_over:
                        print "Starting Playoff game ..."
                        match.PlayWinner()
                        match.series.Update(match.winner)
                        self.stats.Update(match.result.result, 1)
                        print "Game over ...\n"
                    else:
                        print "No game, series is over, Winner: %s\n" % match.series.winner.name
            if self.current_day.number < len(self.days):
                self.current_day = self.days[self.current_day.number]
            else:
                self.current_day.number += 1
        else:
            self.completed = True

    def SwapHomeAway(self):
        curr_day = len(self.days) + 1
        add_days = []
        for day in self.days:
            new_day = Day(curr_day)
            curr_day += 1
            add_days.append(new_day)
            for match in day.matches:
                team1 = match.away_team
                team2 = match.home_team
                new_match = Match(team1, team2, self.tables)
                new_day.Add(new_match)                
        for day in add_days:
            self.days.append(day)

    def RoundRobin(self, teams):
        i = 0
        for team in teams:
            self.rotating_table[i + 1] = teams[i]
            i += 1
        day = 1
        while day <= len(teams) - 1:
            new_day = Day(day)
            self.days.append(new_day)
            match = 1
            while match <= len(teams) / 2:
                if match == 1:
                    team1 = self.rotating_table[match]
                    team2 = self.rotating_table[match + 1]
                else:
                    team1 = self.rotating_table[match + 1]
                    team2 = self.rotating_table[len(teams) - match + 2]
                new_match = Match(team1, team2, self.tables)
                new_day.Add(new_match)                
                match += 1
            day += 1
            # rotate table
            for entry in self.rotating_table.keys():
                if entry > 2:
                    stored_val = self.rotating_table[entry]
                    self.rotating_table[entry] = curr_val
                    curr_val = stored_val
                elif entry == 2:
                    curr_val = self.rotating_table[entry]
                    self.rotating_table[entry] = self.rotating_table[len(teams)]


class Day(object):

    def __init__(self, number):
        self.number = number
        self.matches = []

    def Add(self, match):
        self.matches.append(match)


class Series(object):

    def __init__(self, team1, team2, length):
        self.team1 = team1
        self.team2 = team2
        self.played = 0
        self.length = length
        self.is_over = False
        self.winner = None
        self.loser = None

    def Update(self, winner):
        self.played += 1
        winner.series_wins += 1
        wcount = abs(self.team1.series_wins - self.team2.series_wins)
        threshold = (self.length + 1)/ 2
        if self.played == self.length or wcount == threshold:
            self.is_over = True
            if self.team1.series_wins > self.team2.series_wins:
                self.winner = self.team1
                self.loser = self.team2
            else:
                self.winner = self.team2
                self.loser = self.team1
            print "Series is over, Winner: %s, Loser: %s" % (self.winner.name, self.loser.name)
        
class Match(object):

    def __init__(self, home_team, away_team, tables):
        self.home_team = home_team
        self.away_team = away_team
        self.result = Result(tables)
        self.winner = None
        self.loser = None
        self.series = None

    def Play(self, minutes):
        strength1 = self.home_team.strength
        strength2 = self.away_team.strength
        self.result.score.Display(self.home_team.name, self.away_team.name)
        self.result.Roll(strength1, strength2)
        self.result.score.Generate(self.result.result, minutes)
        home_team = self.home_team.name
        away_team = self.away_team.name
        self.result.score.SimulateScoring(minutes, home_team, away_team)
        self.result.score.Display(home_team, away_team)
        if self.result.score.home > self.result.score.away:
            self.winner = self.home_team
            self.loser = self.away_team
        elif self.result.score.home < self.result.score.away:
            self.winner = self.away_team
            self.loser = self.home_team

    def Update(self):
        if self.result.score.home > self.result.score.away:
            self.home_team.points +=3
        elif self.result.score.home == self.result.score.away:
            self.home_team.points +=1
            self.away_team.points +=1
        else:
            self.away_team.points +=3

    def PlayWinner(self):
        self.Play(90)
        if self.loser == None:
            print "It's a tie, play extra time"
            self.Play(30)
            if self.loser == None:
                print "It's again a tie, penalty kicks"
                self.PenaltyKicks()

    def PenaltyKicks(self):
        print "Penalty kicks ..."
        team1_total = 0
        team2_total = 0
        for i in range(1, 6):
            team1_total += randint(0, 1)
            if (5 - i) < (team2_total - team1_total):
                self.winner = self.away_team
                self.loser = self.home_team
                break
            team2_total += randint(0, 1)
            if (5 - i) < (team1_total - team2_total):
                self.winner = self.home_team
                self.loser = self.away_team
                break
        self.result.score.home += team1_total   
        self.result.score.away += team2_total   
        if team1_total == team2_total:
            while team1_total == team2_total:
                val1 = randint(0, 1)
                val2 = randint(0, 1)
                team1_total += val1
                team2_total += val2
                self.result.score.home += team1_total
                self.result.score.away += team2_total
        if team1_total > team2_total:
            self.winner = self.home_team
            self.loser = self.away_team
        else:
            self.winner = self.away_team
            self.loser = self.home_team
        self.result.score.Display(self.home_team.name, self.away_team.name)


class Result(object):

    def __init__(self, tables):
        self.score = Score(0, 0, tables)
        self.result = None
        self.distribution = tables.result_distr

    def Roll(self, strength1, strength2):
        m1 = uniform(0, strength1)
        m2 = strength2 - (uniform(0, strength2))
        mmax = strength1 + strength2
        md = (m1 + m2)
        for k in sorted(self.distribution.cumulative_distribution.keys()):
            if md <= k * mmax:
                self.result = self.distribution.cumulative_distribution[k]
                break


class Score(object):

    def __init__(self, home, away, tables):
        self.home = home
        self.away = away
        self.score = "0-0"
        self.distributions = {}
        self.distributions["away"] = tables.score_distr["away"]
        self.distributions["draw"] = tables.score_distr["draw"]
        self.distributions["home"] = tables.score_distr["home"]

    def Generate(self, result, minutes):
        table = self.distributions[result]
        m = uniform(0, table.total)
        for k in sorted(table.cumulative_distribution.keys()):
           res = table.cumulative_distribution[k]
           if m <= k:
               self.score = res
               res_obj = re.search(r'(\d)-(\d)', res)
               self.home += int(res_obj.group(1))
               self.away += int(res_obj.group(2))
               break

    def Display(self, home_team, away_team):
        print "%s %d : %s %d" % (home_team, self.home, away_team, self.away)

    def SimulateScoring(self, minutes, home_team, away_team):
        res_obj = re.search(r'(\d)-(\d)', self.score)
        goal_list = { }
        score = { }
        t_list = { }
        score["home"] = int(res_obj.group(1))
        score["away"] = int(res_obj.group(2))
        t_list["home"] = home_team
        t_list["away"] = away_team
        for s in score.keys():
            if score[s] > 0:
                for i in range(score[s]):
                    minute = randint(0, minutes)
                    while minute in goal_list:
                        minute = randint(0, minutes)
                    goal_list[minute] = t_list[s]
        for goal in sorted(goal_list.keys()):
            print "Minute: %s, Goal!!! %s scored" % (goal, goal_list[goal])


class Distribution(object):

    def __init__(self):
        self.frequency_distribution = {}
        self.cumulative_distribution = {}
        self.total = 0

    def Add(self, tag, value):
        self.frequency_distribution[tag] = value
        self.total += value
        #print "Tag: %s, Val: %s, Cumulative Val: %s" % (tag, value, self.total)
        self.cumulative_distribution[self.total] = tag

    def Display(self):
        for k in sorted(self.frequency_distribution.keys()):
            print "Key: %s, Value: %s" % (k, self.frequency_distribution[k])

