import argparse
import yaml


def load_league(league_file):

    with open(league_file, "r") as stream:
        league_dict = yaml.load(stream)
        league_name = list(league_dict.keys())[0]
        print("League: {0}".format(league_name))
        table_obj = Table(league_name)
        years_dict = league_dict[league_name]
        for year in years_dict.keys():
            print("Year: {0}".format(year))
            table_obj.add_year(year)
            pos_dict = years_dict[year]
            for pos in pos_dict.keys():
                table_obj.add_team(pos_dict[pos], year, pos)
                print("Position {0} -> {1}".format(pos, pos_dict[pos]))
        table_obj.display_results()


class League(object):

    def __init__(self, name):
        self.name = name
        self.table = None

    def add_table(self, name):
        print("Adding table {0} ...".format(name))
        self.table = Table(name)


class Table(object):

    def __init__(self, name):
        self.name = name
        self.years = []
        self.years_by_name = {}
        self.teams = []
        self.teams_by_name = {}

    def add_year(self, name):
        print("Adding year {0} ...".format(name))
        new_year = Year(name)
        self.years.append(new_year)
        self.years_by_name[name] = new_year

    def add_team(self, name, year, pos):
        if name in self.teams_by_name.keys():
            print("Adding team {0} ...".format(name))
            new_team = self.teams_by_name[name]
        else:
            print("Adding new team {0} ...".format(name))
            new_team = Team(name)
            self.teams.append(new_team)
            self.teams_by_name[name] = new_team
        self.years_by_name[year].add_team(new_team, pos)
        new_team.update(year, pos)

    def display_results(self):
        points_map = {1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
        idx = 0
        acc_points = 0
        max_agg_points = 0
        years = len(list(self.years))
        max_points = years * points_map.get(1)
        for team in sorted(self.teams, key=lambda idx: idx.points, reverse=True):
            idx += 1
            acc_points += team.points
            max_agg_points += years * points_map.get(idx, 0)
            print("{0:<24}: {1}({2:3.2f}%, {3:3.2f}%)".format(team.name, team.points, 
                                                              team.points/max_points*100,
                                                              acc_points/max_agg_points*100))


class Year(object):

    def __init__(self, name):
        self.name = name
        self.sorted_teams = []

    def add_team(self, team, pos):
        self.sorted_teams.insert(pos - 1, team)


class Team(object):

    def __init__(self, name):
        self.name = name
        self.pos_by_year = {}
        self.points = 0
        self.points_by_pos_table = {1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}

    def update(self, year, pos):
        self.pos_by_year[year] = pos
        self.points += self.points_by_pos_table[pos]

        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="standalone parser")

    parser.add_argument('--league_file', dest='league_file',
                        help='specify league file name',
                        type=str, required=True)

    # do the parsing
    args = parser.parse_known_args()[0]

    load_league(league_file=args.league_file)
