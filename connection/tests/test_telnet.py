""" Module containing the unittest test cases for the connection module.
"""

import re
import libs.comms.mitg_telnet as mitg_telnet
import libs.parametrize as parametrize
import libs.mitg_yaml as mitg_yaml
import libs.eng_mibu_exceptions as eme


class MitgTelnetTestCases(parametrize.ParametrizedTestCase):
    """ Unit test cases object
    """

    def setUp(self):
        """Called at the start of the test.  This method will deterine if the script
        was run as main or not.  If it is not run as main  then it will check if an
        Env. variable is set   so that is can ID the YAML file.  It will also start
        a logger.
        """
        super().setUp()

    def test_create_telnet_connection1(self):
        """
        It will establish a telnet connection and then run the show version command and logout

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # IF there is an issue with the YAML file not having a key,  there will be an
        # excdeption and the test will get an error.
        host = yaml_obj.yaml_dict['devices'][dev_name]['connections']['primary']['ip']
        user = yaml_obj.yaml_dict['devices'][dev_name]['custom']['username']
        passwd = yaml_obj.yaml_dict['devices'][dev_name]['custom']['password']
        pmpt = yaml_obj.yaml_dict['devices'][dev_name]['custom']['prompt']

        # Attempt to log into a MITG device using telnet
        conn = mitg_telnet.TelnetController(host, user, passwd, prompt=pmpt)
        self.assertTrue(isinstance(conn, mitg_telnet.TelnetController),
                        "Unexpected type for conn {0}".format(type(conn)))

        # Log into the device and run a command
        conn.login()
        com_output = conn.run_command("show version")

        # Log out of the chassis
        conn.logout()

        # Make sure there is a line of output one expects
        self.assertTrue(re.search(r'Image Description:', com_output))

    def test_login_failure(self):
        """
        It will establish a telnet connection, but this test will pass an
        invalid username/password  to insure the login raises the correct
        exception

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # IF there is an issue with the YAML file not having a key,  there will be an
        # excdeption and the test will get an error.
        host = yaml_obj.yaml_dict['devices'][dev_name]['connections']['primary']['ip']
        user = yaml_obj.yaml_dict['devices'][dev_name]['custom']['username']
        passwd = "funny_password"
        pmpt = yaml_obj.yaml_dict['devices'][dev_name]['custom']['prompt']

        # Create a Telnet controller object
        conn = mitg_telnet.TelnetController(host, user, passwd, prompt=pmpt)
        self.assertTrue(isinstance(conn, mitg_telnet.TelnetController),
                        "Unexpected type for conn {0}".format(type(conn)))

        with self.assertRaisesRegex(eme.EngTimeoutError, "Timeout Waiting for prompt.*"):
            conn.login()

    def test_create_telnet_connection2(self):
        """
        It will establish a telnet connection and then run the show version command and logout

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        host = yaml_obj.yaml_dict['devices'][dev_name]['connections']['primary']['ip']
        user = yaml_obj.yaml_dict['devices'][dev_name]['custom']['username']
        passwd = yaml_obj.yaml_dict['devices'][dev_name]['custom']['password']
        pmpt = yaml_obj.yaml_dict['devices'][dev_name]['custom']['prompt']

        conn = mitg_telnet.TelnetController(host, user, passwd, prompt=pmpt)
        self.assertTrue(isinstance(conn, mitg_telnet.TelnetController),
                        "Unexpected type for conn {0}".format(type(conn)))
        conn.login()
        res = conn.run_command("show diameter peers full all")
        self.assertTrue(isinstance(res, str), "Unexpect type for res {0}".format(type(res)))
        conn.logout()


if __name__ == "__main__":

    parametrize.parse_and_run_as_main(MitgTelnetTestCases, extended_class=None)

