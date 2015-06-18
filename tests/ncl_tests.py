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
    db = DistributionDB("test.db")
    assert_equal(db.cumulative_total, 0)
    db.Destroy()
