""" Description here
"""

import re
import sqlite3
import logging
import signal
import sys
import traceback
import argparse
import yaml
from random import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

screen_handler = logging.StreamHandler()
screen_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
screen_handler.setFormatter(formatter)

logger.addHandler(screen_handler)


def load_league(league_file):
    """ Read league yaml file and creates conferences, divisions, teams and databases

    :param league_file: yaml file with all teams by conference and division
    :return:
    """

    with open(league_file, "r") as stream:
        league_dict = yaml.load(stream)
        league_name = list(league_dict.keys())[0]
        logger.info("League: {0}".format(league_name))
        league_obj = League(league_name)
        conf_dict = league_dict[league_name].get('conferences')
        for conf_name in conf_dict.keys():
            conf_obj = league_obj.add_conference(conf_name)
            div_dict = conf_dict[conf_name].get('divisions')
            for div_name in div_dict.keys():
                div_obj = conf_obj.add_division(div_name)
                team_dict = div_dict[div_name].get('teams')
                for t_name in team_dict.keys():
                    team_obj = div_obj.add_team(t_name)
                    strength = team_dict[t_name].get('strength')
                    # make it a property
                    team_obj.strength = strength
        db_dict = league_dict[league_name].get('databases')
        for db_name in db_dict.keys():
            db_file_name = re.sub(r' ', '_', db_name.lower())
            db_file_name += ".db"
            logger.info("DB name: {0}".format(db_file_name))
            db_obj = league_obj.create_distribution_db(db_file_name)
            prob_dict = db_dict[db_name].get('probabilities')
            for score, prob in prob_dict.items():
                db_obj.add_score(score, prob)

        return league_obj


class DistributionDB(object):
    """
    Description here
    """

    def __init__(self, db_name):
        """

        :param db_name:
        """

        # supply the special name :memory: to create a database in RAM
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cumulative_total = 0

    def create_table(self):
        """

        :return:
        """
        try:
            self.cursor.execute('''DROP TABLE if exists scores''')
        except sqlite3.OperationalError as err:
            raise RuntimeError("Error: %s" % str(err))
        self.cursor.execute('''CREATE TABLE scores(score TEXT PRIMARY KEY,
            probability FLOAT, cumulative FLOAT, hit INT)''')
        self.conn.commit()

    def add_score(self, score, prob):
        """

        :param score:
        :param prob:
        :return:
        """
        self.cumulative_total += prob
        self.cursor.execute('''INSERT INTO scores(score, probability, cumulative, hit)
            VALUES(?,?,?,?)''', (score, prob, self.cumulative_total, 0))
        self.conn.commit()

    def close(self):
        """

        :return:
        """
        self.conn.close()

    def destroy(self):
        """

        :return:
        """
        self.cursor.execute('''DROP TABLE if exists scores''')
        self.conn.commit()
        self.conn.close()

    def display(self):
        """

        :return:
        """
        total = 0
        draw = 0
        home = 0
        away = 0
        self.cursor.execute("SELECT * FROM scores")
        records = self.cursor.fetchall()
        for record in records:
            actual = record[3]
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
            if total:
                actual = float(record[3])/total
                logger.debug("Actual probability for score {0} = "
                             "{1:.3f} (DB: {2:.3f})".format(score, actual, probability))
        logger.debug("")
        if total:
            home_wins = float(home)/total
            away_wins = float(away)/total
            draws = float(draw)/total
            logger.debug("Home wins probability {:f}".format(home_wins))
            logger.debug("Away wins probability {:f}".format(away_wins))
            logger.debug("Draws probability {:f}".format(draws))
            logger.debug("")

    def get_hit(self, val):
        """

        :param val:
        :return:
        """""
        self.cursor.execute('''SELECT hit FROM scores WHERE score = ?''', (val,))
        return self.cursor.fetchone()[0]

    def get_score(self, val):
        """

        :param val: cumulative distribution
        :return:
        """
        self.cursor.execute('''SELECT score FROM scores WHERE cumulative > ?''', (val,))
        return self.cursor.fetchone()[0]

    def get_prob(self, score):
        """

        :param score: Score
        :return:
        """
        self.cursor.execute('''SELECT probability FROM scores WHERE score = ?''', (score,))
        return self.cursor.fetchone()[0]

    def update(self, tag, value):
        """

        :param tag: score
        :param value: hit
        :return:
        """
        self.cursor.execute('''UPDATE scores SET hit = ? WHERE score = ? ''', (value, tag))
        self.conn.commit()


class Association:
    """
    Description here
    """

    def __init__(self, name):
        """

        :param name:
        """
        self.name = name
        self.teams = []
        self.champion = None
        self.schedule = Schedule()
        signal.signal(signal.SIGPIPE, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def destroy(self):
        """

        :return:
        """
        logger.info("stub for destroy")

    @staticmethod
    def _team_sort(teams):
        """

        :param teams:
        :return:
        """
        sorted_teams = []
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

    def _signal_handler(self, signum, frame):
        """

        :param signum: signal number
        :param frame: frame with the stack
        """
        logger.warning("Interrupt handler called: {0}".format(signum))
        traceback.print_stack(frame)
        self.destroy()
        sys.exit(0)


class League(Association):
    """
    Description here
    """

    def __init__(self, name):
        """

        :param name:
        """
        super().__init__(name)
        self.distributions = {}
        self.conferences = {}

    def add_conference(self, name):
        """

        :param name:
        :return:
        """
        logger.debug("Adding conference {0} ...".format(name))
        new_conf = Conference(name)
        self.conferences[name] = new_conf
        return new_conf

    def create_distribution_db(self, name):
        """

        :param name:
        :return:
        """
        new_db = DistributionDB(name)
        self.distributions[name] = new_db
        new_db.create_table()
        return new_db

    def destroy(self):
        """

        :return:
        """
        for db in self.distributions.values():
            db.destroy()
        
    def display(self):
        """

        :return:
        """
        logger.debug("\n")
        logger.debug("League {0} has {1} conferences:".format(self.name, len(list(self.conferences.keys()))))
        for conf_name, conf in self.conferences.items():
            logger.debug("\t - Conference {0}".format(conf_name))
        for conf in self.conferences.values():
            conf.display()

    def initialize(self):
        """

        :return:
        """
        for conf in self.conferences.values():
            conf.initialize()
        
    def play(self):
        """

        :return:
        """
        # Play Regular Season
        play_on = True
        # state machine?
        while play_on:
            for conf in self.conferences.values():
                conf.regular_season()
                play_on = play_on and not conf.schedule.completed
        # Display Regular Season Results and Setup Playoffs
        for distr_name, distr in self.distributions.items():
            logger.info("Distribution: {0}".format(distr_name))
            distr.display()
        for conf in self.conferences.values():
            conf.setup_playoffs()
        # Play Conference Playoffs
        logger.info("Conference Playoffs start...\n")
        # state machine?
        play_on = True
        while play_on:
            for conf in self.conferences.values():
                conf.play()
                play_on = play_on and not conf.schedule.completed
        # Play Final
        for conf in self.conferences.values():
            self.teams.append(conf.champion)
        self.schedule.reset()
        self.schedule.playoffs(self.teams, 1)
        self.schedule.play(0)
        self.teams = self.schedule.update(self.teams)
        self.champion = self.teams[0]
        logger.info("League Winner: {0}\n".format(self.champion.name))


class Conference(Association):
    """
    Description here
    """

    def __init__(self, name):
        """

        :param name:
        """
        super().__init__(name)
        self.divisions = {}
        self.series_length = 3
        
    def add_division(self, name):
        """

        :param name:
        :return:
        """
        logger.debug("Adding division {0} ...".format(name))
        new_div = Division(name)
        self.divisions[name] = new_div
        return new_div

    def display(self):
        """

        :return:
        """
        logger.debug("Conference {0} has {1} divisions".format(self.name, len(list(self.divisions.keys()))))
        for div_name in self.divisions.keys():
            logger.debug("\t - Division {0}".format(div_name))
        for div in self.divisions.values():
            div.display()

    def initialize(self):
        """

        :return:
        """
        for div in self.divisions.values():
            div.regular_season()

    def play(self):
        """

        :return:
        """
        self.schedule.playoffs(self.teams, self.series_length)
        self.schedule.play(0)
        if self.schedule.completed:
            self.teams = self.schedule.update(self.teams)
            if len(self.teams) > 1:
                self.schedule.reset()
            else:
                self.champion = self.teams[0]
                logger.info("Conference {0} - Playoffs are over".format(self.name))
                logger.info("Winner: {0}\n".format(self.champion.name))

    def regular_season(self):
        """

        :return:
        """
        play_on = True
        for div in self.divisions.values():
            # Regular Season
            div.play()
            play_on = play_on and not div.schedule.completed
        self.schedule.completed = not play_on

    def setup_playoffs(self):
        """

        :return:
        """
        self.schedule.reset()
        # Build Conference Playoff team list
        for div in self.divisions.values():
            self.teams += div.teams[0:int(len(div.teams)/2)]
        self.teams = self._team_sort(self.teams)
        for team in self.teams:
            logger.info("Team {0} made the playoffs".format(team.name))
        logger.info("")


class Division(Association):
    """
    Description here
    """

    def __init__(self, name):
        """

        :param name:
        """
        super().__init__(name)

    def add_team(self, name):
        """

        :param name:
        :return:
        """
        logger.debug("Adding team {0} ...".format(name))
        new_team = Team(name)
        self.teams.append(new_team)
        return new_team

    def display(self):
        """

        :return:
        """
        logger.info("Division {0} Table\n".format(self.name))
        logger.info("--- {:15s} ---".format(self.name))
        for team in self.teams:
            logger.info("{:20s} {:2d}".format(team.name, team.points))
        logger.info("")

    def regular_season(self):
        """

        :return:
        """
        self.schedule.round_robin(self.teams)
        self.schedule.display(self.name)

    def play(self):
        """

        :return:
        """
        self.schedule.play(90)
        self.teams = self._team_sort(self.teams)
        self.display()


class Team(object):
    """
    Description here
    """

    def __init__(self, name):
        """

        :param name:
        """
        self.name = name
        self.strength = 0
        self.points = 0
        self.series_wins = 0


class Schedule(object):

    def __init__(self):
        """

        """
        self.days = []
        self.current_day = None
        self.completed = False
        self.series_list = []
 
    def display(self, name):
        """

        :param name:
        :return:
        """
        logger.debug("-------------- {0} Schedule: --------------".format(name))
        for day in self.days:
            for match in day.matches:
                home = match.home_team.name
                away = match.away_team.name
                logger.debug("Day {0} - Match: {1} vs {2}".format(day.number, home, away))
        logger.debug("")

    def reset(self):
        """

        :return:
        """
        self.completed = False
        self.series_list = []
        self.days = []
        self.current_day = None

    def play(self, minutes):
        """

        :param minutes:
        :return:
        """
        logger.info("Day: {0}\n".format(self.current_day.number))
        for match in self.current_day.matches:
            if match.series and match.series.is_over:
                logger.debug("Series is over, Winner: {0}\n".format(match.series.winner.name))
                continue
            if minutes > 0:
                logger.debug("Starting {0}-minute game ...".format(minutes))
                match.play(minutes)
                match.update()
            else:
                logger.debug("Starting game ...")
                match.play_winner()
                match.series.update(match.winner)
            logger.debug("Game over ...")
            logger.info("")
        if self.current_day.number < len(self.days):
            logger.info("Day: {0} of {1}\n".format(self.current_day.number, len(self.days)))
            self.current_day = self.days[self.current_day.number]
        else:
            self.completed = True

    def playoffs(self, teams, series_length):
        """

        :param teams:
        :param series_length:
        :return:
        """
        if len(self.series_list) > 0:
            return
        for i in range(0, int(len(teams)/2)):
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
                new_day.add(match)
        self.current_day = self.days[0]

    def round_robin(self, teams):
        """

        :param teams:
        :return:
        """

        second_half = []
        rotating_table = {}
        for team_idx in range(0, len(teams)):
            rotating_table[team_idx + 1] = teams[team_idx]
            team_idx += 1
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
                new_day.add(new_match)
                associated_match = Match(team2, team1)
                associated_day.add(associated_match)
                match += 1
            day += 1
            # rotate table
            curr_val = 0
            for entry in rotating_table.keys():
                if entry == 2:
                    curr_val = rotating_table[entry]
                    rotating_table[entry] = rotating_table[len(teams)]
                elif entry > 2:
                    stored_val = rotating_table[entry]
                    rotating_table[entry] = curr_val
                    curr_val = stored_val
                else:
                    logger.debug("Nothing to do".format(entry))
        self.days += second_half 
        self.current_day = self.days[0]

    def update(self, teams):
        """

        :param teams:
        :return:
        """
        for s in self.series_list:
            loser = teams.index(s.loser)
            teams.pop(loser)
        return teams


class Day(object):
    """
    Description here
    """

    def __init__(self, number):
        """

        :param number:
        """
        self.number = number
        self.matches = []

    def add(self, match):
        """

        :param match:
        :return:
        """
        self.matches.append(match)


class Series(object):
    """
    Description here
    """

    def __init__(self, team1, team2, length):
        """

        :param team1:
        :param team2:
        :param length:
        """

        self.team1 = team1
        self.team2 = team2
        self.played = 0
        self.length = length
        self.is_over = False
        self.winner = None
        self.loser = None

    def update(self, winner):
        """

        :param winner:
        :return:
        """
        self.played += 1
        winner.series_wins += 1
        wcount = abs(self.team1.series_wins - self.team2.series_wins)
        threshold = (self.length + 1) / 2
        if self.played == self.length or wcount == threshold:
            self.is_over = True
            if self.team1.series_wins > self.team2.series_wins:
                self.winner = self.team1
                self.loser = self.team2
            else:
                self.winner = self.team2
                self.loser = self.team1
            logger.debug("Series is over, Winner: {0}, Loser: {1}".format(self.winner.name, self.loser.name))
        

class Match(object):
    """
    Description here
    """

    def __init__(self, home_team, away_team):
        """

        :param home_team:
        :param away_team:
        """
        self.home_team = home_team
        self.away_team = away_team
        self.score = Score()
        self.winner = None
        self.loser = None
        self.series = None

    def play(self, minutes):
        """

        :param minutes:
        :return:
        """
        strength1 = self.home_team.strength
        strength2 = self.away_team.strength
        # Generate the score
        if minutes == 30:
            self.score.generate("extra_time")
        else:
            self.score.generate("regular_time")
        home_team = self.home_team.name
        away_team = self.away_team.name
        logger.info("Home Team {0} strength: {1}".format(home_team, strength1))
        logger.info("Away Team {0} strength: {1}".format(away_team, strength2))
        self.score.simulate_scoring(minutes, home_team, away_team)
        self.score.display(home_team, away_team)
        if self.score.home > self.score.away:
            self.winner = self.home_team
            self.loser = self.away_team
        elif self.score.home < self.score.away:
            self.winner = self.away_team
            self.loser = self.home_team

    def update(self):
        """

        :return:
        """
        if self.score.home > self.score.away:
            self.home_team.points += 3
        elif self.score.home == self.score.away:
            self.home_team.points += 1
            self.away_team.points += 1
        else:
            self.away_team.points += 3

    def play_winner(self):
        """

        :return:
        """
        self.play(90)
        if self.loser is None:
            logger.info("It's a tie, play extra time")
            self.play(30)
            if self.loser is None:
                logger.info("It's again a tie, penalty kicks")
                self.penalty_kicks()

    def penalty_kicks(self):
        """

        :return:
        """
        logger.debug("Penalty kicks ...")
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
        self.score.display(self.home_team.name, self.away_team.name)


class Score(object):
    """
    Description here
    """

    def __init__(self):
        """

        """
        self.home = 0
        self.away = 0
        self.score = "0-0"

    def generate(self, name):
        """

        :param name:
        :return:
        """
        db_name = name + ".db"
        db = DistributionDB(db_name)
        roll = uniform(0, 1.0)
        self.score = db.get_score(roll)
        hit = db.get_hit(self.score) + 1
        logger.debug("Number of hits for score %s: %s" % (self.score, hit))
        db.update(self.score, hit)
        db.close()
        res_obj = re.search(r'(\d)-(\d)', self.score)
        self.home += int(res_obj.group(1))
        self.away += int(res_obj.group(2))

    def display(self, home_team, away_team):
        """

        :param home_team:
        :param away_team:
        :return:
        """
        logger.info("{0} {1}: {2} {3}".format(home_team, self.home, away_team, self.away))

    def simulate_scoring(self, minutes, home_team, away_team):
        """

        :param minutes:
        :param home_team:
        :param away_team:
        :return:
        """

        res_obj = re.search(r'(\d)-(\d)', self.score)
        goal_list = {}
        score = {"home": int(res_obj.group(1)), "away": int(res_obj.group(2))}
        t_list = {"home": home_team, "away": away_team}
        for s in score.keys():
            if score[s] > 0:
                for i in range(score[s]):
                    minute = randint(0, minutes)
                    while minute in goal_list:
                        minute = randint(0, minutes)
                    goal_list[minute] = t_list[s]
        for goal in sorted(goal_list.keys()):
            logger.debug("Minute: {0}, Goal!!! {1} scored".format(goal, goal_list[goal]))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="standalone parser")

    parser.add_argument('--league_file', dest='league_file',
                        help='specify league file name',
                        type=str, required=True)

    # do the parsing
    args = parser.parse_known_args()[0]

    league = load_league(league_file=args.league_file)
    league.display()
    league.initialize()
    league.play()
    league.destroy()
