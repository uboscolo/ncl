from nose.tools import *
from ncl.ncl import DistributionDB

def setup():
    pass

def teardown():
    pass

def test_basic():
    db = DistributionDB("test.db")
    assert_equal (db.cumulative_total, 0)
    db.Destroy()
