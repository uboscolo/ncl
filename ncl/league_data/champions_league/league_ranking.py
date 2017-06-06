import argparse
import yaml


def load_league(league_file):

    with open(league_file, "r") as stream:
        league_dict = yaml.load(stream)
        league_name = list(league_dict.keys())[0]
        print("League: {0}".format(league_name))
        new_league = League(league_name)

        conf_dict = league_dict[league_name].get('conferences')
        for conf in conf_dict.keys():
            print("Conference: {0}".format(conf))
            conf_obj = Conference(conf)
            new_league.conferences[conf] = conf_obj
            div_dict = conf_dict[conf].get('divisions')
            for div in div_dict.keys():
                print("Division: {0}".format(div))
                div_obj = Division(div)
                conf_obj.divisions[div] = div_obj
                country_dict = div_dict[div].get('countries')
                for country in country_dict.keys():
                    print("Country: {0}".format(country))
                    new_country = Country(country)
                    new_country.conference = conf_obj
                    new_country.division = div_obj
                    new_country.league = country_dict[country]
                    new_league.countries[country] = new_country

        pos_dict = league_dict[league_name].get('positions')
        for pos in pos_dict.keys():
            print("Position: {0}".format(pos))
            new_league.points_table[pos] = pos_dict[pos].get('points')

        years_dict = league_dict[league_name].get('years')
        for year in years_dict.keys():
            print("Year: {0}".format(year))
            teams_dict = years_dict[year].get('teams')
            for team in teams_dict.keys():
                country = teams_dict[team].get('country')
                country_obj = new_league.countries.get(country)
                div_obj = country_obj.division
                if team not in div_obj.teams.keys():
                    new_team = Team(team)
                else:
                    new_team = div_obj.teams.get(team)
                new_team.country = country_obj
                country_obj.teams[team] = new_team 
                country_obj.division.teams[team] = new_team
                curr_points = new_league.points_table[(teams_dict[team].get('position'))]
                new_team.points += curr_points
                print("Team: {0}, Points: {1}".format(new_team.name, new_team.points))
                if year not in new_league.points_per_year:
                    new_league.points_per_year[year] = 0
                new_league.points_per_year[year] += curr_points
        for year, points in new_league.points_per_year.items():
            print("Year: {0}, Points: {1}".format(year, points))
        total_points = 0
        all_teams = []
        for country in new_league.countries.values():
            for team in country.teams.values():
                country.points += team.points
                all_teams.append(team)
            total_points += country.points
        sorted_all_teams = sorted(all_teams, key=lambda idx: idx.points, reverse=True)
        for team in sorted_all_teams:
            print("Team: {0}, Points: {1}, Position: {2}, Strength: {3:.4f}".format(team.name, team.points, sorted_all_teams.index(team) + 1, team.points/total_points*100))
        for country in sorted(new_league.countries.values(), key=lambda idx: idx.points, reverse=True):
            print("Country: {0}, Points: {1}".format(country.name, country.points))
            for team in sorted(country.teams.values(), key=lambda idx: idx.points, reverse=True):
                print("Team: {0}, Points: {1}, Strength: {2:.4f}".format(team.name, team.points, team.points/total_points*100))
        for conf_obj in new_league.conferences.values():
            for div_obj in conf_obj.divisions.values():
                for team in div_obj.teams.values():
                    conf_obj.points += team.points
                    div_obj.points += team.points
                print("Division {0}, Points {1}".format(div_obj.name, div_obj.points))
            print("Conference {0}, Points {1}".format(conf_obj.name, conf_obj.points))


class League:

    def __init__(self, name):
        self.name = name
        self.table = None
        self.points_table = {}
        self.points_per_year = {}
        self.countries = {}
        self.conferences = {}


class Conference:

    def __init__(self, name):
        self.name = name
        self.points = 0
        self.divisions = {}


class Division:

    def __init__(self, name):
        self.name = name
        self.points = 0
        self.teams = {}


class Team:

    def __init__(self, name):
        self.name = name
        self.country = None
        self.points = 0


class Country:

    def __init__(self, name):
        self.name = name
        self.league = None
        self.conference = None
        self.division = None
        self.teams = {}
        self.points = 0


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="standalone parser")

    parser.add_argument('--league_file', dest='league_file',
                        help='specify league file name',
                        type=str, required=True)

    # do the parsing
    args = parser.parse_known_args()[0]

    load_league(league_file=args.league_file)
