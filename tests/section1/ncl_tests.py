from nose.tools import *
import os
from ncl.ncl import *

def setup():
    try:
        os.remove("regular_season_game.db")
        os.remove("extra_time.db")
    except:
        pass
    assert_false(os.path.exists("regular_season_game.db") or 
                 os.path.exists("extra_time.db"))

def teardown():
    try:
        os.remove("regular_season_game.db")
        os.remove("extra_time.db")
    except:
        pass
    assert_false(os.path.exists("regular_season_game.db") or 
                 os.path.exists("extra_time.db"))

def test_8():
    """Run Ncl with a 8-team league"""
    try:
        xml_file = open("tests/section1/ncl_8teams.xml", "r")
        p = Parser(xml_file)
        league = p.ParseXml()
        league.Display()
        league.Initialize()
        league.Play()
        league.Destroy()
    except IOError:
        print "Could not open file"
        raise

