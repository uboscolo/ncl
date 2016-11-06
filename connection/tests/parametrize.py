""" Module containing the unittest parametrization class
to be inherited by unitest test cases
"""
import unittest
import time
import logging
import argparse
import os
import libs.mitg_yaml as mitg_yaml


def parse_and_run_as_main(basic_class, extended_class):
    """
    Invokes a generic parser for unittest whose inputs are a yaml file and an optional test name.
    The function takes two args, basic_class and extended_class, and by default it runs the tests
    that are defined inside basic_class
    :param basic_class: Name of the basic class whose tests are run by default
    :param extended_class: Name of the extended class, whose tests are only run if "run_extended" is passed
    """

    parser = argparse.ArgumentParser(description="unittest parser")
    parser.add_argument('-i', '--input', dest='input_file',
                        help='Chassis Input file in YAML format', action='store',
                        required=True)
    parser.add_argument('-t', '--test', dest='test_name',
                        help='Name of test to run', action='store',
                        required=False, default='run_basic')
    parser.add_argument('-c', '--callmodel', dest='callmodel_file',
                        help='Call model input file in YAML format', action='store',
                        required=False)
    parser.add_argument('-d', '--dut_name', dest='dut_name',
                        help='dut name', action='store',
                        required=False, default=None)
    parser.add_argument('-l', '--loglevel', help='set the logging level (debug|info|warning|error|critical)', default='info')

    # do the parsing
    args = parser.parse_args()

    # need to open input file
    suite = unittest.TestSuite()
    
    numeric_level = getattr(logging, args.loglevel.upper())

    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(args.loglevel))

    # Setcommand line up logging
    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename='test_chassis.log',
                        filemode='w',
                        level=numeric_level)

    # Get the full path of the YAML file
    # yaml_file_loc = mitg_yaml.find_yaml_file(args.input_file)

    if args.test_name == 'run_basic':
        suite.addTest(ParametrizedTestCase.parametrize(basic_class,
                                                       args.input_file,
                                                       run_as_main=True,
                                                       callmodel_file=args.callmodel_file,
                                                       dut_name=args.dut_name))
    elif args.test_name == 'run_extended':
        suite.addTest(ParametrizedTestCase.parametrize(extended_class,
                                                       args.input_file,
                                                       run_as_main=True,
                                                       callmodel_file=args.callmodel_file,
                                                       dut_name=args.dut_name))
    else:
        if extended_class:
            exec_class = extended_class
        else:
            exec_class = basic_class
        suite.addTest(
            ParametrizedTestCase.parametrize(exec_class,
                                             args.input_file,
                                             args.test_name,
                                             run_as_main=True,
                                             callmodel_file=args.callmodel_file,
                                             dut_name=args.dut_name))
    unittest.TextTestRunner(verbosity=2).run(suite)


def get_yaml_file_loc(input_file):
    """
    get the location of the yaml file
    :param input_file:
    :return: the file location
    """
    yaml_file_loc = mitg_yaml.find_yaml_file(input_file)
    return yaml_file_loc


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """
    def __init__(self, method_name='runTest', param=None, run_as_main=False, **kwargs):
        """
        initalize reference.

        :param TestClass method_name: Class of sub-class
        :param ANY param: Parameter

        """
        super(ParametrizedTestCase, self).__init__(method_name)
        self.param = param
        self.run_as_main_program = run_as_main
        self.callmodel_file = kwargs.get('callmodel_file', None)
        self.dut_name = kwargs.get('dut_name', None)

    def setUp(self):
        """

        :return:
        """
        super().setUp()
        self.startTime = time.time()
        global yaml_file_loc
        if not self.run_as_main_program:
            # Check to see if Env variable is set.
            self.param = os.environ.get("TESTBED_YAML")
            if not self.param:
                self.fail("Running not as main and Env variable TESTBED_YAML is not set")
            self.callmodel_file = os.environ.get("MITG_CALL_MODEL_FILE")

    def tearDown(self):
        """

        :return:
        """
        super().tearDown()
        delta = time.time() - self.startTime
        print("%s: %.3f" % (self.id(), delta))

    @staticmethod
    def parametrize(testcase_klass, param=None, test_name=None, run_as_main=False, **kwargs):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.

        :param TestClass testcase_klass: Class of tests
        :param str param: Parameter, this is the device params
        :param str test_name: Test Name, If one is not specified all tests are run
        :param bool run_as_main: if the test is running as main
        """
        testloader = unittest.TestLoader()
        suite = unittest.TestSuite()
        if test_name:
            testnames = [test_name]
        else:
            testnames = testloader.getTestCaseNames(testcase_klass)

        for name in testnames:
            suite.addTest(testcase_klass(name, param=param, run_as_main=run_as_main, **kwargs))
        return suite

