import argparse
import yaml


class Organization:

    def __init__(self, name):
        self.__name = name
        self.__teams = {}

    @property
    def name(self):
        """ """
        return self.__name

    @property
    def teams(self):
        """ """
        return [team for team in self.__teams.values()]

    def add_team(self, team):
        """ """
        if not self.__teams.get(team.name):
            self.__teams[team.name] = team
 
    def get_team_by_name(self, name):
        """ """
        return self.__teams.get(name)

    def team_ranking(self):
        """ """
        for pos, team in enumerate(sorted(self.__teams.values(), key=lambda idx: idx.get_points(), reverse=True)):
            if team.get_points():
                print("{} - {}: {}".format(pos+1, team.name, team.get_points()))
 

class League(Organization):

    def __init__(self, name):
        self.__countries = {}
        self.__conferences = {}
        super().__init__(name=name)
    
    @property
    def countries(self):
        """ """
        return [country for country in self.__countries.values()]

    @property
    def conferences(self):
        """ """
        return [conf for conf in self.__conferences.values()]

    def add_country(self, country):
        """ """
        if not self.__countries.get(country.name):
            self.__countries[country.name] = country

    def add_conference(self, conference):
        """ """
        if not self.__conferences.get(conference.name):
            self.__conferences[conference.name] = conference

    def country_ranking(self):
        """ """
        for pos, country in enumerate(sorted(self.__countries.values(), key=lambda idx: idx.get_points(), reverse=True)):
            if country.get_points():
                print("{} - {}: {}".format(pos+1, country.name, country.get_points()))
 

class Country(Organization):

    def __init__(self, name):
        self.league = None
        self.conference = None
        self.division = None
        self.__points = {}
        super().__init__(name=name)

    def add_points(self, year, points):
        """ """
        if not self.__points.get(year):
            self.__points[year] = 0
        
        self.__points[year] += points

    def get_points(self, year=None):
        """ """
        points = 0
        if year:
            points = self.__points.get(year, 0)
        else:
            for y_points in self.__points.values():
                points += y_points

        return points
    
 
class Conference(Organization):

    def __init__(self, name):
        self.divisions = {}
        super().__init__(name=name)


class Division(Organization):

    def __init__(self, name):
        super().__init__(name=name)


class Team:

    def __init__(self, name):
        self.name = name
        self.country = None
        self.__points = {}

    def add_points(self, year, points):
        """ """
        if not self.__points.get(year):
            self.__points[year] = 0
        
        self.__points[year] += points
    
        if self.country:
            self.country.add_points(year=year, points=points)

    def get_points(self, year=None):
        """ """
        points = 0
        if year:
            points = self.__points.get(year, 0)
        else:
            for y_points in self.__points.values():
                points += y_points

        return points
 

def load_teams(team_file, league_file):
    """ """

    new_league = None
    with open(team_file, "r") as s_teams, open(league_file, "r") as s_league:
        leagues = yaml.load(s_league)
        league = next(league for league in leagues)
        new_league = League(league)
       
        points = leagues[league].get("points")
        years = leagues[league].get("years")

        d_teams = yaml.load(s_teams)
        org = next(org for org in d_teams)
       
        confs = d_teams[org].get("conferences")
        for conf in confs:
            new_conf = Conference(name=conf)
            divs = confs[conf].get("divisions")
            new_league.add_conference(conference=new_conf)
            for div in divs:
                new_div = Division(div)
                new_conf.divisions[div] = new_div
                countries = divs[div].get("countries")
                for country in countries:
                    new_country = Country(country)
                    new_country.conference = conf
                    new_country.division = div
                    new_country.league = countries[country].get("league")
                    new_league.add_country(country=new_country)
                    teams = countries[country].get("teams")
                    for team in teams:
                        new_team = Team(team)
                        new_div.add_team(team=new_team)
                        new_team.country = new_country
                        new_country.add_team(team=new_team)
                        new_league.add_team(team=new_team)
        for year, results in years.items():
            for result, team_list in results.items():
                curr_points = points.get(result).get("points")
                for team_name in team_list:
                    curr_team = new_league.get_team_by_name(name=team_name)
                    if not curr_team:
                        raise ValueError(team_name, curr_team)
                    curr_team.add_points(year=year, points=curr_points)

    new_league.team_ranking()
    new_league.country_ranking()
    for country in new_league.countries:
        print("{}: {}".format(country.name, country.league))
        country.team_ranking()
        


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="standalone parser")

    parser.add_argument('--teams', 
                        dest='teams',
                        help='Teams file',
                        type=str, 
                        required=True)
    parser.add_argument('--league', 
                        dest='league',
                        help='league file',
                        type=str, 
                        required=True)

    # do the parsing
    args = parser.parse_known_args()[0]

    load_teams(team_file=args.teams, league_file=args.league)
