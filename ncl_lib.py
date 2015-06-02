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

    def initialize(self):
        self.score_distr["away"] = Distribution()
        self.score_distr["draw"] = Distribution()
        self.score_distr["home"] = Distribution()
        # 0
        self.score_distr["draw"].add("0-0", 0.085)
        # 1
        self.score_distr["home"].add("1-0", 0.125)
        self.score_distr["away"].add("0-1", 0.065)
        # 2
        self.score_distr["draw"].add("1-1", 0.120)
        self.score_distr["home"].add("2-0", 0.090)
        self.score_distr["away"].add("0-2", 0.050)
        # 3
        self.score_distr["home"].add("2-1", 0.093)
        self.score_distr["away"].add("1-2", 0.053)
        self.score_distr["home"].add("3-0", 0.045)
        self.score_distr["away"].add("0-3", 0.015)
        # 4
        self.score_distr["draw"].add("2-2", 0.045)
        self.score_distr["home"].add("4-0", 0.025)
        self.score_distr["away"].add("0-4", 0.015)
        self.score_distr["home"].add("3-1", 0.045)
        self.score_distr["away"].add("1-3", 0.025)
        # 5
        self.score_distr["home"].add("3-2", 0.020)
        self.score_distr["away"].add("2-3", 0.015)
        self.score_distr["home"].add("4-1", 0.015)
        self.score_distr["away"].add("1-4", 0.010)
        self.score_distr["home"].add("5-0", 0.005)
        self.score_distr["away"].add("0-5", 0.003)
        # 6
        self.score_distr["draw"].add("3-3", 0.007)
        self.score_distr["home"].add("4-2", 0.007)
        self.score_distr["away"].add("2-4", 0.002)
        self.score_distr["home"].add("5-1", 0.005)
        self.score_distr["away"].add("1-5", 0.002)
        self.score_distr["home"].add("6-0", 0.002)
        self.score_distr["away"].add("0-6", 0.001)
        # 7
        self.score_distr["home"].add("4-3", 0.003)
        self.score_distr["away"].add("3-4", 0.002)
        self.score_distr["home"].add("5-2", 0.001)
        self.score_distr["away"].add("2-5", 0.001)
        self.score_distr["home"].add("6-1", 0.001)
        self.score_distr["away"].add("1-6", 0.001)
        self.score_distr["home"].add("7-0", 0.001)
        # results
        self.result_distr.add("away", 0.32)
        self.result_distr.add("draw", 0.19)
        self.result_distr.add("home", 0.49)

 
class League(object):

    def __init__(self, name):
        self.name = name
        self.tables = DistributionTables("Tables")
        self.conferences = [ ]
        self.conferences_table_by_name = { } 

    def __Final(self):
        team1 = self.conferences[0].conference_champion
        team2 = self.conferences[1].conference_champion
        final = Match(team1, team2, self.tables)
        print "\n League %s Final\n" % self.name
        final.play_winner()
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
        self.tables.initialize()
        for conf in self.conferences:
            conf.Initialize(self.tables)
            for div in conf.divisions:
                div.Initialize(self.tables)
                div.schedule.Display(div.name)
        
    def Play(self):
        # Play Regular Season
        play_on = True
        while play_on:
            for conf in self.conferences:
                for div in conf.divisions:
                    # Regular Season
                    div.Play()
                    play_on = play_on and not div.schedule_completed
        # Display Regular Season Results and Setup Playoffs
        for conf in self.conferences:
            for div in conf.divisions:
                div.stats.Display(div.name)
            conf.Setup_playoff_schedule()
        # Play Conference Playoffs
        play_on = True
        print "\n Conference Playoffs start..."
        while play_on:
            for conf in self.conferences:
                # Playoffs
                conf.Play()
                play_on = play_on and not conf.schedule_completed
        # Play Final
        self.__Final()


class Conference(League):

    def __init__(self, name):
        super(Conference, self).__init__(name)
        self.current_day = 0
        self.schedule_completed = False
        self.divisions = [ ]
        self.divisions_table_by_name = { }
        self.playoff_list = [ ]
        self.series_len = 3
        self.series_list = [ ]
        self.schedule = None
        self.conference_champion = None

    def Add(self, name):
        print "Adding division %s ..." % name
        new_div = Division(name)
        self.divisions.append(new_div) 
        self.divisions_table_by_name[name] = new_div

    def Display(self):
        print "Conference %s has %d divisions:" % (
            self.name, len(self.divisions))
        for div in self.divisions:
            print "\t - Division %s" % (div.name)
        for div in self.divisions:
            div.Display()

    def Initialize(self, tables):
        self.tables = tables
        self.schedule = Schedule(tables)

    def Setup_playoff_schedule(self):
        for div in self.divisions:
            for team in div.playoff_teams:
                if len(self.playoff_list) > 0:
                    found = 0
                    for pos in range(len(self.playoff_list)):
                        if team.points >= self.playoff_list[pos].points:
                            self.playoff_list.insert(pos, team)
                            found = 1
                            break
                    if found == 0: 
                        self.playoff_list.append(team)
                else:
                    self.playoff_list.append(team)
        dlen = len(self.playoff_list)
        if dlen % 2:
            print "Number of Playoff teams not even (%s)" % dlen
            sys.exit(1)
        for i in range(0, int(math.log(dlen, 2)) * self.series_len):
            new_day = Day(i + 1)
            self.schedule.days.append(new_day)
            
    def Play(self):
        if self.current_day < len(self.schedule.days):
            day = self.schedule.days[self.current_day]
            print "\nDay: %d - Conference: %s\n" % (day.number, self.name)
            if len(self.series_list) == 0:
                for i in range(0, len(self.playoff_list)/2):
                    team1 = self.playoff_list[i]
                    team2 = self.playoff_list[len(self.playoff_list) - 1 - i]
                    new_series = Series(team1, team2, self.series_len)
                    self.series_list.append(new_series)
            for s in self.series_list:
                if s.played % 2:
                    match = Match(s.team2, s.team1, self.tables)
                else:
                    match = Match(s.team1, s.team2, self.tables)
                match.series = s
                day.add_match(match)
            for match in day.matches:
                mnum = match.series.played + 1
                mlen = len(self.playoff_list)
                if mlen > 8:
                    print "Conference Round of 16 - Match %s" % (mnum)
                elif mlen > 4:
                    print "Conference Quarterfinals - Match %s" % (mnum)
                elif mlen > 2:
                    print "Conference Semifinals - Match %s" % (mnum)
                else:
                    print "Conference Finals - Match %s" % (mnum)
                match.play_winner()
                match.series.update(match.winner)
                if match.series.is_over:
                    loser = self.playoff_list.index(match.series.loser)
                    self.playoff_list.pop(loser)
                    self.series_list.remove(match.series)
                print "Game over ...\n"
                if mlen == 2:
                    self.conference_champion = match.winner        
            self.current_day += 1
        else:
            print "Conference %s - Playoffs are over" % self.name
            print "Winner: %s\n" % (self.conference_champion.name)
            self.schedule_completed = True


class Division(Conference):

    def __init__(self, name):
        super(Division, self).__init__(name)
        self.teams = [ ]
        self.playoff_teams = [ ]
        self.table = Table()
        self.stats = Statistics("Division Statistics")

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
        self.schedule.round_robin(self.teams)
        self.schedule.swap_home_away()
        self.stats.Add("home")
        self.stats.Add("away")
        self.stats.Add("draw")

    def Play(self):
        if self.current_day < len(self.schedule.days):
            day = self.schedule.days[self.current_day]
            print "\nDay: %d - Division: %s\n" % (day.number, self.name)
            for match in day.matches:
                print "Starting regular season game ..."
                match.play(90)
                match.update_points()
                self.stats.Update(match.result.result, 1)
                print "Game over ...\n"
            self.table.Sort(self.teams)
            self.table.Display(day, self.name)
            self.current_day += 1
        else:
            print "\n Division %s - Regular Season is over\n" % self.name
            teams = self.table.sorted_teams
            self.playoff_teams = teams[0:len(teams)/2]
            for team in self.playoff_teams:
                print "Team %s made the playoffs" % team.name
            self.schedule_completed = True


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

    def Display(self, day, name):
        print "\nDay %d Table\n" % day.number
        print "--- {:15s} ---".format(name) 
        for team in self.sorted_teams:
            print "{:20s} {:2d}".format(team.name, team.points)


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
        for t in self.table.keys():
            print "%s: %s" % (t, self.table[t])


class Schedule(object):

    def __init__(self, tables):
        self.rotating_table = { }
        self.days = []
        self.tables = tables
 
    def Display(self, div_name):
        print "----------- Division %s Schedule: -----------" % div_name
        for day in self.days:
            for match in day.matches:
                home = match.home_team.name
                away = match.away_team.name
                print "Day %s - Match: %s vs %s" % (day.number, home, away) 

    def swap_home_away(self):
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
                new_day.add_match(new_match)                
        for day in add_days:
            self.days.append(day)

    def round_robin(self, teams):
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
                new_day.add_match(new_match)                
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

    def add_match(self, match):
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

    def update(self, winner):
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
        
class Match(object):

    def __init__(self, home_team, away_team, tables):
        self.home_team = home_team
        self.away_team = away_team
        self.result = Result(tables)
        self.winner = None
        self.loser = None
        self.series = None

    def play(self, minutes):
        strength1 = self.home_team.strength
        strength2 = self.away_team.strength
        self.result.score.display(self.home_team.name, self.away_team.name)
        self.result.roll(strength1, strength2)
        self.result.score.generate(self.result.result, minutes)
        home_team = self.home_team.name
        away_team = self.away_team.name
        self.result.score.simulate_scoring(minutes, home_team, away_team)
        self.result.score.display(home_team, away_team)
        if self.result.score.home > self.result.score.away:
            self.winner = self.home_team
            self.loser = self.away_team
        elif self.result.score.home < self.result.score.away:
            self.winner = self.away_team
            self.loser = self.home_team

    def update_points(self):
        if self.result.score.home > self.result.score.away:
            self.home_team.points +=3
        elif self.result.score.home == self.result.score.away:
            self.home_team.points +=1
            self.away_team.points +=1
        else:
            self.away_team.points +=3

    def play_winner(self):
        self.play(90)
        if self.loser == None:
            print "It's a tie, play extra time"
            self.play(30)
            if self.loser == None:
                print "It's again a tie, penalty kicks"
                self.penalty_kicks()

    def penalty_kicks(self):
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
        self.result.score.display(self.home_team.name, self.away_team.name)


class Result(object):

    def __init__(self, tables):
        self.score = Score(0, 0, tables)
        self.result = None
        self.distribution = tables.result_distr

    def roll(self, strength1, strength2):
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

    def generate(self, result, minutes):
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

    def display(self, home_team, away_team):
        print "%s %d : %s %d" % (home_team, self.home, away_team, self.away)

    def simulate_scoring(self, minutes, home_team, away_team):
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

    def add(self, tag, value):
        self.frequency_distribution[tag] = value
        self.total += value
        #print "Tag: %s, Val: %s, Cumulative Val: %s" % (tag, value, self.total)
        self.cumulative_distribution[self.total] = tag

    def display(self):
        for k in sorted(self.frequency_distribution.keys()):
            print "Key: %s, Value: %s" % (k, self.frequency_distribution[k])

