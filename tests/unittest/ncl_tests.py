from nose.tools import *
import os
from ncl.ncl import DistributionDB

def setup():
    try:
        os.remove("test.db")
    except:
        pass
    assert_false(os.path.exists("test.db"))

def teardown():
    try:
        os.remove("test.db")
    except:
        pass
    assert_false(os.path.exists("test.db"))


def test_distribution1():
    """Check DistributionDB"""
    db = DistributionDB("test.db")
    assert_equal(db.cumulative_total, 0)
    db.Destroy()

def test_distribution2():
    """Check CreateTable in DistributionDB"""
    db = DistributionDB("test.db")
    db.CreateTable()   
    db.Destroy()

