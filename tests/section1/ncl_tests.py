from nose.tools import *
import os
from ncl.ncl import *

def setup():
    try:
        if os.path.exists("regular_season_game.db"):
            os.remove("regular_season_game.db")
        if os.path.exists("extra_time.db"):
            os.remove("extra_time.db")
        if os.path.exists("/tmp/test8;log"):
            os.remove("/tmp/test8.log")
        if os.path.exists("/tmp/test64;log"):
            os.remove("/tmp/test64.log")
    except:
        raise

def teardown():
    try:
        if os.path.exists("regular_season_game.db"):
            os.remove("regular_season_game.db")
        if os.path.exists("extra_time.db"):
            os.remove("extra_time.db")
    except:
        raise


def test_8():
    """Run Ncl with a 8-team league"""
    try:
        logger = Logger("extensive", "/tmp/test8.log").logger
        SetLogger(logger)
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

def test_64():
    """Run Ncl with a 64-team league"""
    try:
        logger = Logger("extensive", "/tmp/test64.log").logger
        SetLogger(logger)
        xml_file = open("tests/section1/ncl_64teams.xml", "r")
        p = Parser(xml_file)
        league = p.ParseXml()
        league.Display()
        league.Initialize()
        league.Play()
        league.Destroy()
    except IOError:
        print "Could not open file"
        raise
