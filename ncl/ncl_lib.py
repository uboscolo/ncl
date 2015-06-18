from random import *
import math
import re
import sqlite3
import os
import signal
import sys


class DistributionDB(object):

    def __init__(self, db_name):
        #supply the special name :memory: to create a database in RAM
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cumulative_total = 0

    def CreateTable(self):
        try:
            self.cursor.execute('''DROP TABLE if exists scores''')
        except sqlite3.OperationalError as err:
            print "Error: %s" % str(err)
        self.cursor.execute('''CREATE TABLE scores(score TEXT PRIMARY KEY,
            probability FLOAT, hit INT)''')
        self.conn.commit()

    def AddScore(self, s, p):
        self.cumulative_total += p
        self.cursor.execute('''INSERT INTO scores(score, probability, hit)
            VALUES(?,?,?)''', (s, self.cumulative_total, 0))
        self.conn.commit()

    def Close(self):
        self.conn.close()

    def Destroy(self):
        self.cursor.execute('''DROP TABLE scores''')
        self.conn.commit()
        self.conn.close()

    def Display(self):
        total = 0
        draw = 0
        home = 0
        away = 0
        self.cursor.execute("SELECT * FROM scores")
        records = self.cursor.fetchall()
        for record in records:
            actual = record[2]
            total += actual
            res_obj = re.search(r'(\d)-(\d)', record[0])
            if int(res_obj.group(1)) == int(res_obj.group(2)): 
                draw += actual
            elif int(res_obj.group(1)) > int(res_obj.group(2)):
                home += actual
            else:
                away += actual
        for record in records:
            score = record[0]
            probability = record[1]
            actual = float(record[2])/total
            print "Score %s actual probabilty %s" % (score, actual)
        print ""
        home_wins = float(home)/total
        away_wins = float(away)/total
        draws = float(draw)/total
        print "Home wins have probabilty %f" % home_wins
        print "Away wins have probabilty %f" % away_wins
        print "Draws have probabilty %f" % draws
        print ""

    def GetHit(self, sample):
        self.cursor.execute('''SELECT hit FROM scores 
            WHERE score = ?''', (sample,))
        return self.cursor.fetchone()[0]

    def GetScore(self, sample):
        self.cursor.execute('''SELECT score FROM scores 
            WHERE probability > ?''', (sample,))
        return self.cursor.fetchone()[0]

    def Update(self, tag, value):
        self.cursor.execute('''UPDATE scores SET hit = ? WHERE score = ? ''',
            (value, tag))
        self.conn.commit()


class Association(object):

    def __init__(self, name):
        self.name = name
        self.teams = [ ]
        self.champion = None
        self.schedule = Schedule()

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


class League(Association):

    def __init__(self, name):
        super(League, self).__init__(name)
        #signal.signal(signal.SIGPIPE, self.__SignalHandler)
        #signal.signal(signal.SIGINT, self.__SignalHandler)
        self.distributions = [ ]
        self.distributions_by_name = { }
        self.conferences = [ ]
        self.conferences_table_by_name = { } 

    #def __SignalHandler(self, signum, frame):
    #    print "Interrupt handler called: %s" % (signum)
    #    self.Destroy
    #    sys.exit(0)

    def Add(self, name):
        print "Adding conference %s ..." % name
        new_conf = Conference(name)
        self.conferences.append(new_conf)
        self.conferences_table_by_name[name] = new_conf

    def CreateDistribution(self, name):
        db_name = name + ".db"
        new_db = DistributionDB(db_name)
        self.distributions.append(new_db)
        self.distributions_by_name[name] = new_db
        new_db.CreateTable()

    def Destroy(self):
        for db in self.distributions:
            db.Destroy()
        
    def Display(self):
        print "\n"
        print "League %s has %d conferences:" % (
            self.name, len(self.conferences))
        for conf in self.conferences:
            print "\t - Conference %s" % (conf.name)
        for conf in self.conferences:
            conf.Display()

    def Initialize(self):
        for conf in self.conferences:
            conf.Initialize()
        
    def Play(self):
        # Play Regular Season
        play_on = True
        # state machine?
        while play_on:
            for conf in self.conferences:
                conf.RegularSeason()
                play_on = play_on and not conf.schedule.completed
        # Display Regular Season Results and Setup Playoffs
        self.distributions_by_name["regular_season_game"].Display()
        for conf in self.conferences:
            conf.SetupPlayoffs()
        # Play Conference Playoffs
        print "\n Conference Playoffs start..."
        # state machine?
        play_on = True
        while play_on:
            for conf in self.conferences:
                conf.Play()
                play_on = play_on and not conf.schedule.completed
        # Play Final
        for conf in self.conferences:
            self.teams.append(conf.champion)
        self.schedule.Reset()
        self.schedule.Playoffs(self.teams, 1)
        self.schedule.Play(0)
        self.teams = self.schedule.Update(self.teams)
        self.champion = self.teams[0]
        print "League Winner: %s\n" % self.champion.name


class Conference(Association):

    def __init__(self, name):
        super(Conference, self).__init__(name)
        self.divisions = [ ]
        self.divisions_table_by_name = { }
        self.series_length = 3
        
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

    def Initialize(self):
        for div in self.divisions:
            div.RegularSeason()
            div.schedule.Display(div.name)

    def Play(self):
        self.schedule.Playoffs(self.teams, self.series_length)
        self.schedule.Play(0)
        if self.schedule.completed:
            self.teams = self.schedule.Update(self.teams)
            if len(self.teams) > 1:
                self.schedule.Reset()
            else:
                self.champion = self.teams[0]
                print "Conference %s - Playoffs are over" % self.name
                print "Winner: %s\n" % self.champion.name

    def RegularSeason(self):
        play_on = True
        for div in self.divisions:
            # Regular Season
            div.Play()
            play_on = play_on and not div.schedule.completed
        self.schedule.completed = not play_on

    def SetupPlayoffs(self):
        self.schedule.Reset()
        # Build Conference Playoff team list
        for div in self.divisions:
            self.teams += div.teams[0:len(div.teams)/2]
        self.teams = self.Sort(self.teams)
        for team in self.teams:
            print "Team %s made the playoffs" % team.name
        print ""


class Division(Association):

    def __init__(self, name):
        super(Division, self).__init__(name)

    def Add(self, name, strength):
        print "Adding team %s with strength: %d ..." % (name, strength)
        new_team = Team(name, strength)
        self.teams.append(new_team) 

    def Display(self):
        print "Table\n"
        print "--- {:15s} ---".format(self.name) 
        for team in self.teams:
            print "{:20s} {:2d}".format(team.name, team.points)
        print ""

    def RegularSeason(self):
        self.schedule.RoundRobin(self.teams)

    def Play(self):
        self.schedule.Play(90)
        self.teams = self.Sort(self.teams)
        self.Display()


class Team(object):

    def __init__(self, name, strength):
        self.name = name
        self.strength = strength
        self.points = 0
        self.series_wins = 0


class Schedule(object):

    def __init__(self):
        self.days = [ ]
        self.current_day = None
        self.completed = False
        self.series_list = [ ]
 
    def Display(self, name):
        print "-------------- %s Schedule: --------------" % name
        for day in self.days:
            for match in day.matches:
                home = match.home_team.name
                away = match.away_team.name
                print "Day %s - Match: %s vs %s" % (day.number, home, away) 
        print ""

    def Reset(self):
        self.completed = False
        self.series_list = [ ]
        self.days = [ ]
        self.current_day = None

    def Play(self, minutes):
        print "Day: %d\n" % (self.current_day.number)
        for match in self.current_day.matches:
            if match.series and match.series.is_over:
                print "Series is over, Winner: %s\n" % match.series.winner.name
                next
            if minutes > 0:
                print "Starting %s-minute game ..." % (minutes)
                match.Play(minutes)
                match.Update()
                print "Game over ...\n"
            else:
                print "Starting game ..."
                match.PlayWinner()
                match.series.Update(match.winner)
            print "Game over ...\n"
        if self.current_day.number < len(self.days):
            self.current_day = self.days[self.current_day.number]
        else:
            self.completed = True

    def Playoffs(self, teams, series_length):
        if len(self.series_list) > 0:
            return
        for i in range(0, len(teams)/2):
            team1 = teams[i]
            team2 = teams[len(teams) - 1 - i]
            new_series = Series(team1, team2, series_length)
            self.series_list.append(new_series)
        for i in range(1, series_length + 1):
            new_day = Day(i)
            self.days.append(new_day)
            for s in self.series_list:
                if (i - 1) % 2:
                    match = Match(s.team2, s.team1)
                else:
                    match = Match(s.team1, s.team2)
                match.series = s
                new_day.Add(match)
        self.current_day = self.days[0]

    def RoundRobin(self, teams):
        i = 0
        second_half = [ ]
        rotating_table = { }
        for team in teams:
            rotating_table[i + 1] = teams[i]
            i += 1
        day = 1
        while day <= len(teams) - 1:
            # first half of the season
            new_day = Day(day)
            self.days.append(new_day)
            # second half
            day2 = day + len(teams) - 1
            associated_day = Day(day2)
            second_half.append(associated_day)
            match = 1
            while match <= len(teams) / 2:
                if match == 1:
                    team1 = rotating_table[match]
                    team2 = rotating_table[match + 1]
                else:
                    team1 = rotating_table[match + 1]
                    team2 = rotating_table[len(teams) - match + 2]
                new_match = Match(team1, team2)
                new_day.Add(new_match)                
                associated_match = Match(team2, team1)
                associated_day.Add(associated_match)
                match += 1
            day += 1
            # rotate table
            for entry in rotating_table.keys():
                if entry > 2:
                    stored_val = rotating_table[entry]
                    rotating_table[entry] = curr_val
                    curr_val = stored_val
                elif entry == 2:
                    curr_val = rotating_table[entry]
                    rotating_table[entry] = rotating_table[len(teams)]
        self.days += second_half 
        self.current_day = self.days[0]

    def Update(self, teams):
        for s in self.series_list:
            loser = teams.index(s.loser)
            teams.pop(loser)
        return teams


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
            print "Series is over, Winner: %s, Loser: %s" % (self.winner.name, 
                self.loser.name)
        

class Match(object):

    def __init__(self, home_team, away_team):
        self.home_team = home_team
        self.away_team = away_team
        self.score = Score()
        self.winner = None
        self.loser = None
        self.series = None

    def Play(self, minutes):
        strength1 = self.home_team.strength
        strength2 = self.away_team.strength
        self.score.Display(self.home_team.name, self.away_team.name)
        # Generate the score
        if minutes == 30:
            self.score.Generate("extra_time")
        else:
            self.score.Generate("regular_season_game")
        home_team = self.home_team.name
        away_team = self.away_team.name
        self.score.SimulateScoring(minutes, home_team, away_team)
        self.score.Display(home_team, away_team)
        if self.score.home > self.score.away:
            self.winner = self.home_team
            self.loser = self.away_team
        elif self.score.home < self.score.away:
            self.winner = self.away_team
            self.loser = self.home_team

    def Update(self):
        if self.score.home > self.score.away:
            self.home_team.points +=3
        elif self.score.home == self.score.away:
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
        self.score.home += team1_total   
        self.score.away += team2_total   
        if team1_total == team2_total:
            while team1_total == team2_total:
                val1 = randint(0, 1)
                val2 = randint(0, 1)
                team1_total += val1
                team2_total += val2
                self.score.home += team1_total
                self.score.away += team2_total
        if team1_total > team2_total:
            self.winner = self.home_team
            self.loser = self.away_team
        else:
            self.winner = self.away_team
            self.loser = self.home_team
        self.score.Display(self.home_team.name, self.away_team.name)


class Score(object):

    def __init__(self):
        self.home = 0
        self.away = 0
        self.score = "0-0"

    def Generate(self, name):
        db_name = name + ".db"
        db = DistributionDB(db_name)
        m = uniform(0, 1.0)
        #print "Random number %s (Max=%s)" % (m, 1.0)
        self.score = db.GetScore(m)
        hit = db.GetHit(self.score) + 1
        print "Number of hits for score %s: %s" % (self.score, hit)
        db.Update(self.score, hit)
        db.Close()
        #print "Score %s" % (self.score)
        res_obj = re.search(r'(\d)-(\d)', self.score)
        self.home += int(res_obj.group(1))
        self.away += int(res_obj.group(2))

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
