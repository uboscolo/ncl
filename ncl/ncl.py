#!/usr/bin/env python
import sys
import os
import optparse
from ncl_lib import *

def main(argv):
    parser = optparse.OptionParser(usage="usage: %prog [options] xml_file")
    parser.add_option('-v', '--verbose',
                  dest="verbose",
                  default=False,
                  help="turn on verbosity",
                  action="store_true",
                  )
    opts, remainder = parser.parse_args()
    if len(remainder) > 1:
        parser.error("wrong number of arguments")

    xml_file = remainder[0]
    if not os.path.exists(xml_file) or not os.path.isfile(xml_file):
        print "invalid file %s" % xml_file
        sys.exit(1)

    try:
        p = Parser(xml_file)
        league = p.ParseXml()
        league.Display()
        league.Initialize()
        league.Play()
        league.Destroy()
    except IOError as err:
        print str(err)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
