""" Description here
"""

import re
import sqlite3
import logging
import signal
import sys
import traceback
import argparse
import random
import yaml

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

SCREEN_HANDLER = logging.StreamHandler()
SCREEN_HANDLER.setLevel(logging.DEBUG)

FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
SCREEN_HANDLER.setFormatter(FORMATTER)

LOGGER.addHandler(SCREEN_HANDLER)


def load_league(league_file):
    """ Read league yaml file and creates conferences, divisions, teams and databases

    :param league_file: yaml file with all teams by conference and division
    :return:
    """

    with open(league_file, "r") as stream:
        league_dict = yaml.load(stream)
        league_name = list(league_dict.keys())[0]
        LOGGER.info(msg="League: {0}".format(league_name))
        league_obj = League(league_name)
        league_obj.playoffs = league_dict[league_name].get('playoffs', False)
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
            LOGGER.info(msg="DB name: {0}".format(db_file_name))
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
                LOGGER.debug(msg="Actual probability for score {0} = "
                             "{1:.3f} (DB: {2:.3f})".format(score, actual, probability))
        LOGGER.debug("")
        if total:
            home_wins = float(home)/total
            away_wins = float(away)/total
            draws = float(draw)/total
            LOGGER.debug(msg="Home wins {:2.2f}% (50%)".format(home_wins*100))
            LOGGER.debug(msg="Away wins {:2.2f}% (25%)".format(away_wins*100))
            LOGGER.debug(msg="Draws {:2.2f}% (25%)".format(draws*100))
            LOGGER.debug("")

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
        LOGGER.info("stub for destroy")

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
                for pos in sorted_teams:
                    if team.points >= pos.points:
                        pos_index = sorted_teams.index(pos)
                        sorted_teams.insert(pos_index, team)
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
        LOGGER.warning(msg="Interrupt handler called: {0}".format(signum))
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
        self.playoffs = False
        self.final_series = []
        self.series_length = 1

    def add_conference(self, name):
        """

        :param name:
        :return:
        """
        LOGGER.debug(msg="Adding conference {0} ...".format(name))
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
        for db_obj in self.distributions.values():
            db_obj.destroy()

    def display(self):
        """

        :return:
        """
        LOGGER.debug("\n")
        LOGGER.debug(msg="League {0} has {1} "
                     "conferences:".format(self.name,
                                           len(list(self.conferences.keys()))))
        for conf_name, conf in self.conferences.items():
            LOGGER.debug(msg="\t - Conference {0}".format(conf_name))
        for conf in self.conferences.values():
            conf.display()

    def initialize(self):
        """

        :return:
        """
        for conf in self.conferences.values():
            conf.initialize()

    def setup_final(self):
        """

        :return:
        """
        self.schedule.reset()
        for conf in self.conferences.values():
            self.teams.append(conf.champion)
        self.teams = self._team_sort(self.teams)
        for team in self.teams:
            LOGGER.info(msg="Team {0} made the final".format(team.name))
        for idx in range(0, int(len(self.teams)/2)):
            team1 = self.teams[idx]
            team2 = self.teams[len(self.teams) - 1 - idx]
            new_series = Series(team1, team2, self.series_length)
            self.final_series.append(new_series)
        self.schedule.playoffs(self.final_series, self.series_length)
        LOGGER.info("")

    def play_final(self):
        """

        :return:
        """
        # self.schedule.playoffs(self.teams, self.series_length)
        self.schedule.play(0)
        self.champion = self.final_series[0].winner
        LOGGER.info(msg="League Winner: {0}\n".format(self.champion.name))

    def play(self):
        """

        :return:
        """
        # Play Regular Season
        LOGGER.info("Regular Season starts...\n")
        completed = False
        while not completed:
            for conf in self.conferences.values():
                completed = conf.regular_season() or completed
        # Display Regular Season Results and Setup Playoffs
        for distr_name, distr in self.distributions.items():
            LOGGER.info(msg="Distribution: {0}".format(distr_name))
            distr.display()
        if not self.playoffs:
            LOGGER.info("Season is over")
            return
        for conf in self.conferences.values():
            conf.build_playoffs()
            conf.build_playouts()
        # Play Conference Playoffs
        completed = False
        LOGGER.info("Playoffs start...\n")
        while not completed:
            for conf in self.conferences.values():
                # conf.setup_playoffs()
                # conf.setup_playouts()
                conf.setup_postseason()
                completed = conf.postseason() or completed
        # Play Final
        self.setup_final()
        self.play_final()


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
        self.playoff_teams = []
        self.playout_teams = []
        self.playoff_series = []
        self.playout_series = []
        self.series_length = 3

    def add_division(self, name):
        """

        :param name:
        :return:
        """
        LOGGER.debug(msg="Adding division {0} ...".format(name))
        new_div = Division(name)
        self.divisions[name] = new_div
        return new_div

    def display(self):
        """

        :return:
        """
        LOGGER.debug(msg="Conference {0} has {1} "
                     "divisions".format(self.name,
                                        len(list(self.divisions.keys()))))
        for div_name in self.divisions.keys():
            LOGGER.debug(msg="\t - Division {0}".format(div_name))
        for div in self.divisions.values():
            div.display()

    def initialize(self):
        """

        :return:
        """
        for div in self.divisions.values():
            div.regular_season()

    def regular_season(self):
        """

        :return: whether schedule is completed
        :rtype: bool
        """
        if not self.schedule.completed:
            play_on = True
            for div in self.divisions.values():
                # Regular Season
                div.play()
                play_on = play_on and not div.schedule.completed
            self.schedule.completed = not play_on
        return self.schedule.completed

    def build_playoffs(self):
        """

        :return:
        """
        for div in self.divisions.values():
            self.playoff_teams += div.teams[0:int(len(div.teams)/2)]
        self.playoff_teams = self._team_sort(self.playoff_teams)

    def build_playouts(self):
        """

        :return:
        """
        for div in self.divisions.values():
            self.playout_teams += div.teams[int(len(div.teams)/2):]
        self.playout_teams = self._team_sort(self.playout_teams)

    def setup_postseason(self):
        """

        :return:
        """
        if self.playoff_series or self.playout_series:
            LOGGER.info("Still playing playoff or playout series")
            return
        self.schedule.reset()
        self.setup_playoffs()
        self.setup_playouts()
        self.schedule.playoffs(self.playoff_series + self.playout_series, self.series_length)
        LOGGER.info("")

    def setup_playoffs(self):
        """

        :return:
        """
        # if self.playoff_series:
        #    LOGGER.info("Still playing playoff series")
        #    return
        # self.schedule.reset()
        for team in self.playoff_teams:
            LOGGER.info(msg="Team {0} in the playoffs".format(team.name))
        for idx in range(0, int(len(self.playoff_teams) / 2)):
            team1 = self.playoff_teams[idx]
            team2 = self.playoff_teams[len(self.teams) - 1 - idx]
            LOGGER.info("Setting up series, team1={}, team2={}".format(team1.name, team2.name))
            new_series = Series(team1, team2, self.series_length)
            self.playoff_series.append(new_series)
        # self.schedule.playoffs(self.playoff_series, self.series_length)
        # LOGGER.info("")

    def setup_playouts(self):
        """

        :return:
        """
        # if self.playout_series:
        #    LOGGER.info("Still playing playout series")
        #    return
        # self.schedule.reset()
        for team in self.playout_teams:
            LOGGER.info(msg="Team {0} in the playouts".format(team.name))
        for idx in range(0, int(len(self.playout_teams) / 2)):
            team1 = self.playout_teams[idx]
            team2 = self.playout_teams[len(self.teams) - 1 - idx]
            LOGGER.info("Setting up series, team1={}, team2={}".format(team1.name, team2.name))
            new_series = Series(team1, team2, self.series_length)
            self.playout_series.append(new_series)
        # self.schedule.playoffs(self.playout_series, self.series_length)
        # LOGGER.info("")

    def postseason(self):
        """

        :return: whether schedule is completed
        :rtype: bool
        """
        # self.schedule.playoffs(self.teams, self.series_length)
        self.schedule.play(0)
        if self.schedule.completed:
            # Playoffs
            if len(self.playoff_series) > 1:
                LOGGER.info("More playoffs, series={}".format(len(self.playoff_series)))
                self.playoff_teams = []
                for series in self.playoff_series:
                    self.playoff_teams.append(series.winner)
                self.playoff_series = []
                self.schedule.completed = False
            else:
                self.champion = self.playoff_teams[0]
                LOGGER.info(msg="Conference {0} - Playoffs are over".format(self.name))
                LOGGER.info(msg="Winner: {0}\n".format(self.champion.name))
            # Playouts
            if len(self.playout_series) > 2:
                LOGGER.info("More playouts, series={}".format(len(self.playout_series)))
                self.playout_teams = []
                for series in self.playout_series:
                    self.playout_teams.append(series.loser)
                self.playout_series = []
                self.schedule.completed = False
            else:
                # Teams to be relegated
                for team in self.playout_teams:
                    LOGGER.info("Team {0} to be relegated: {0}".format(team.name))
        return self.schedule.completed


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
        LOGGER.debug(msg="Adding team {0} ...".format(name))
        new_team = Team(name)
        self.teams.append(new_team)
        return new_team

    def display(self):
        """

        :return:
        """
        LOGGER.info(msg="Division {0} Table\n".format(self.name))
        LOGGER.info(msg="--- {:15s} ---".format(self.name))
        for team in self.teams:
            LOGGER.info(msg="{:20s} {:2d}".format(team.name, team.points))
        LOGGER.info("")

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
    """
    Description here
    """

    def __init__(self):
        """
        Description here
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
        LOGGER.debug(msg="-------------- {0} Schedule: --------------".format(name))
        for day in self.days:
            for match in day.matches:
                home = match.home_team.name
                away = match.away_team.name
                LOGGER.debug(msg="Day {0} - Match: {1} vs {2}".format(day.number, home, away))
        LOGGER.debug("")

    def reset(self):
        """

        :return:
        """
        self.completed = False
        self.days = []
        self.current_day = None

    def play(self, minutes):
        """

        :param minutes:
        :return:
        """
        LOGGER.info(msg="Day: {0}\n".format(self.current_day.number))
        for match in self.current_day.matches:
            if match.series and match.series.is_over:
                LOGGER.debug(msg="Series is over, Winner: {0}\n".format(match.series.winner.name))
                continue
            if minutes > 0:
                LOGGER.debug(msg="Starting {0}-minute game ...".format(minutes))
                match.play(minutes)
                match.update()
            else:
                LOGGER.debug("Starting game ...")
                match.play_winner()
                match.series.update(match.winner)
            LOGGER.debug("Game over ...")
            LOGGER.info("")
        if self.current_day.number < len(self.days):
            LOGGER.info(msg="Day: {0} of {1}\n".format(self.current_day.number, len(self.days)))
            self.current_day = self.days[self.current_day.number]
        else:
            self.completed = True

    def playoffs(self, series_list, series_length):
        """

        :param series_list:
        :param series_length:
        :return:
        """
        for idx in range(1, series_length + 1):
            new_day = Day(idx)
            self.days.append(new_day)
            for series in series_list:
                if (idx - 1) % 2:
                    match = Match(series.team2, series.team1)
                else:
                    match = Match(series.team1, series.team2)
                if series_length == 1:
                    # It's the final
                    match.disable_home_advantage()
                match.series = series
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

        self.days += second_half
        self.current_day = self.days[0]


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
            LOGGER.debug(msg="Series is over, Winner: {0}, "
                         "Loser: {1}".format(self.winner.name,
                                             self.loser.name))


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
        self.__home_advantage = True

    def disable_home_advantage(self):
        """

        """
        self.__home_advantage = False

    def play(self, minutes, home_advantage=True):
        """
        Each team has a strength. Home team strength is doubled before game.
        For each team, strength is "adjusted" by picking a random number between zero and team strength.
        This gives a chance to ay team to win a game
        Strength ratio is computed as Home team strength divided by Away team strength.
        If strength ratio is greater than 2, then Home team wins 
        If strength ratio is smaller than 0.5, then Away team wins 
        A tie will occur otherwise.

        :param minutes:
        :return:
        """
        strength1 = self.home_team.strength
        strength2 = self.away_team.strength
        home_team = self.home_team.name
        away_team = self.away_team.name
        LOGGER.info(msg="Home Team {0} strength: {1}".format(home_team, strength1))
        LOGGER.info(msg="Away Team {0} strength: {1}".format(away_team, strength2))
        if self.__home_advantage:
            strength1 *= 2
            LOGGER.info(msg="Home Team {0} strength doubles: {1}".format(home_team, strength1))
        # Luck factor
        strength1 = random.uniform(0, strength1)
        strength2 = random.uniform(0, strength2)
        LOGGER.info(msg="Home Team {0} adjusted strength: {1}".format(home_team, strength1))
        LOGGER.info(msg="Away Team {0} adjusted strength: {1}".format(away_team, strength2))
        # Relative strength
        total_strength = strength1 + strength2
        rel_strength1 = strength1 / total_strength
        rel_strength2 = strength2 / total_strength
        LOGGER.info(msg="Home Team {0} relative strength: {1}".format(home_team, rel_strength1))
        LOGGER.info(msg="Away Team {0} relative strength: {1}".format(away_team, rel_strength2))
        rel_strength_ratio = rel_strength1 / rel_strength2
        LOGGER.info(msg="Relative strenght ratio = {0}".format(rel_strength_ratio))
        if rel_strength_ratio > 2:
            result = "home"
        elif rel_strength_ratio < 0.5:
            result = "away"
        else:
            result = "draw"
        score = self.__get_score(result=result, minutes=minutes)
        if minutes == 30:
            self.score.update(name="extra_time", score=score)
            self.score.simulate_scoring(score, minutes, 90, home_team, away_team)
        else:
            self.score.update(name="regular_time", score=score)
            self.score.simulate_scoring(score, minutes, 0, home_team, away_team)
        self.score.display(home_team, away_team)
        if self.score.home > self.score.away:
            self.winner = self.home_team
            self.loser = self.away_team
        elif self.score.home < self.score.away:
            self.winner = self.away_team
            self.loser = self.home_team
        else:
            self.winner = None
            self.loser = None

    def __get_score(self, result, minutes):
        """

        :param result:
        :param minutes:
        :return:
        """
        LOGGER.info("Result is {0}".format(result))
        while True:
            if minutes == 30:
                score = self.score.generate("extra_time")
            else:
                score = self.score.generate("regular_time")
            winner = self.score.get_winner(score)
            if winner == result:
                return score

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
            LOGGER.info("It's a tie, play extra time")
            self.play(30)
            if self.loser is None:
                LOGGER.info("It's again a tie, penalty kicks")
                self.penalty_kicks()

    def penalty_kicks(self):
        """

        :return:
        """
        LOGGER.debug("Penalty kicks ...")
        team1_total = 0
        team2_total = 0
        for i in range(1, 6):
            team1_total += random.randint(0, 1)
            if (5 - i) < (team2_total - team1_total):
                self.winner = self.away_team
                self.loser = self.home_team
                break
            team2_total += random.randint(0, 1)
            if (5 - i) < (team1_total - team2_total):
                self.winner = self.home_team
                self.loser = self.away_team
                break
        self.score.home += team1_total
        self.score.away += team2_total
        if team1_total == team2_total:
            while team1_total == team2_total:
                val1 = random.randint(0, 1)
                val2 = random.randint(0, 1)
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

    @staticmethod
    def generate(name):
        """

        :param name: DB name
        :return:
        """
        db_name = name + ".db"
        db_obj = DistributionDB(db_name)
        roll = random.uniform(0, 1.0)
        score = db_obj.get_score(roll)
        # hit = db_obj.get_hit(score) + 1
        # LOGGER.debug(msg="Number of hits for score %s: %s" % (score, hit))
        # db_obj.update(score, hit)
        # db_obj.close()
        return score

    @staticmethod
    def get_winner(score):
        """

        :param score:
        :return:
        """
        res_obj = re.search(r'(\d)-(\d)', score)
        if int(res_obj.group(1)) > int(res_obj.group(2)):
            res = "home"
        elif int(res_obj.group(2)) > int(res_obj.group(1)):
            res = "away"
        else:
            res = "draw"
        return res

    def update(self, name, score):
        """

        :param name: DB name
        :param score:
        :return:
        """
        db_name = name + ".db"
        db_obj = DistributionDB(db_name)
        hit = db_obj.get_hit(score) + 1
        LOGGER.debug(msg="Number of hits for score %s: %s" % (score, hit))
        db_obj.update(score, hit)
        db_obj.close()
        res_obj = re.search(r'(\d)-(\d)', score)
        self.home += int(res_obj.group(1))
        self.away += int(res_obj.group(2))

    def display(self, home_team, away_team):
        """

        :param home_team:
        :param away_team:
        :return:
        """
        LOGGER.info(msg="{0} {1}: {2} {3}".format(home_team, self.home, away_team, self.away))

    @staticmethod
    def simulate_scoring(score, minutes, offset, home_team, away_team):
        """

        :param score:
        :param minutes:
        :param home_team:
        :param away_team:
        :param offset:
        :return:
        """

        res_obj = re.search(r'(\d)-(\d)', score)

        goal_list = {}
        score_dict = {"home": int(res_obj.group(1)), "away": int(res_obj.group(2))}
        t_list = {"home": home_team, "away": away_team}
        for team in score_dict.keys():
            if score_dict[team] > 0:
                for i in range(score_dict[team]):
                    minute = random.randint(offset, minutes+offset)
                    if minute in goal_list:
                        minute = random.randint(offset, minutes+offset)
                    goal_list[minute] = t_list[team]
        for goal in sorted(goal_list.keys()):
            LOGGER.debug(msg="Minute: {0}, Goal!!! {1} scored".format(goal, goal_list[goal]))

if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description="standalone parser")

    PARSER.add_argument('--league_file', dest='league_file',
                        help='specify league file name',
                        type=str, required=True)

    # do the parsing
    ARGS = PARSER.parse_known_args()[0]

    LEAGUE = load_league(league_file=ARGS.league_file)
    LEAGUE.display()
    LEAGUE.initialize()
    LEAGUE.play()
    LEAGUE.destroy()
