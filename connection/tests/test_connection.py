""" Module containing the unittest test cases for the connection module.  The connection
module is used the
"""

import re
import libs.mitg_yaml as mitg_yaml
import libs.comms.connection as connection
import libs.parametrize as parametrize
import libs.eng_mibu_exceptions as eme


class ConnectionTestCases(parametrize.ParametrizedTestCase):
    """ Unit test cases object
    """

    def setUp(self):
        """Called at the start of the test.  This method will deterine if the script
        was run as main or not.  If it is not run as main  then it will check if an
        Env. variable is set   so that is can ID the YAML file.  It will also start
        a logger.
        """

        super().setUp()

    def test_create_telnet_connection(self):
        """
        Test that will create a Telnet Connection to the device.  It will perform
        many tests in this one method.  This will cut down the time of constantly
        connecting to a device.

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to telnet
        con_dict["proto"] = "telnet"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        # Run all the boxer related tests
        self.boxer_test(conn_obj, "telnet")

    def test_create_ssh_connection(self):
        """
        Test that will create a Telnet Connection to the device.  It will perform
        many tests in this one method.  This will cut down the time of constantly
        connecting to a device.

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to SSH
        con_dict["proto"] = "ssh"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        # Run all the boxer related tests
        self.boxer_test(conn_obj, "ssh")

    def test_fail_telnet_connection(self):
        """
        Test that will fail to create a Telnet Connection to the device, by using a non valid
        prompt

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to telnet
        con_dict["proto"] = "telnet"
        con_dict["prompt"] = "bogus"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        conn_obj._mitg_generic_prompt = 'bogus'

        self.assertRaises(eme.EngConnectionError, conn_obj.login, timeout=10)

    def test_fail_telnet_command(self):
        """
        Test that will fail to run a command in a Telnet Connection to the device, by using a non valid
        prompt

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to telnet
        con_dict["proto"] = "telnet"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        conn_obj.login()

        conn_obj.set_prompt("bogus")

        self.assertRaises(eme.EngConnectionError, conn_obj.run_command, "show version", timeout=10)

    def test_fail_ssh_connection(self):
        """
        Test that will fail to create a Ssh Connection to the device, by using a non valid
        prompt

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to telnet
        con_dict["proto"] = "ssh"
        con_dict["prompt"] = "bogus"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        conn_obj._mitg_generic_prompt = 'bogus'

        self.assertRaises(eme.EngConnectionError, conn_obj.login, timeout=10)

    def test_fail_ssh_command(self):
        """
        Test that will fail to run a command in a Ssh Connection to the device, by using a non valid
        prompt

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Change the protocol to telnet
        con_dict["proto"] = "ssh"

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        conn_obj.login()

        conn_obj.set_prompt("bogus")

        self.assertRaises(eme.EngConnectionError, conn_obj.run_command, "show version", timeout=10)

    def test_create_ssh_ts_connection(self):
        """
        Test that will create a Telnet Connection to the device.  It will perform
        many tests in this one method.  This will cut down the time of constantly
        connecting to a device.

        :return: None
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection dict for cli5
        con_dict = yaml_obj.get_connection_dict(dev_name, connection_name="cli5")

        # Create the connection object to the device
        conn_obj = connection.ASR5500Connection(con_dict)

        # Run all the boxer related tests
        try:
            self.boxer_test(conn_obj, "ssh")
        except eme.EngMibuException as err:
            print("boxer_test failed on cli5: {0}".format(err))

            # Get the connection dict for cli6
            con_dict = yaml_obj.get_connection_dict(dev_name, connection_name="cli6")

            # Create the connection object to the device
            conn_obj = connection.ASR5500Connection(con_dict)

            self.boxer_test(conn_obj, "ssh")

    def boxer_test(self, conn_obj, proto_name):
        """Common tests to run on boxer based chassis
        """

        # Log into the device, run a command and check the output to validate connection.
        conn_obj.login()
        cmd_out = conn_obj.run_command("show version")
        self.assertTrue("Image Version" in cmd_out)

        # Enter priveledged mode
        conn_obj.enable_priv_mode()

        # Insure the protocol type is telnet.  The default connection is telnet
        proto = conn_obj.get_protocol()
        self.assertTrue(proto == proto_name, msg="Protocol {0} did not match {1}".format(proto,
                                                                                         proto_name))

        # Attempt to run a linux command
        conn_obj.linux_mode()
        cmd_out = conn_obj.run_command("ls /")

        # There should be an HD raid directory
        self.assertTrue("hd-raid" in cmd_out)

        # AFIO mode
        conn_obj.afio_mode()
        cmd_output = conn_obj.run_command("help")
        self.assertTrue('Will display help' in cmd_output, msg='Unexpected AFIO help'.format(cmd_output))

        # exit AFIO mode
        conn_obj.exit_afio_mode()

        # Go back to boxer mode
        conn_obj.cli_mode()

        # Get the slot info.  The following block of code is here just to get
        # a valid slot for a DPC card  that the SW will connect to.
        cmd_output = conn_obj.run_command("show card table")

        # get the first slot with a DPC card
        slot = 0
        for line in cmd_output.split('\n'):
            line_match = re.search(r'(\d{1,2}):\s+DPC.*(Standby|Active)', line)
            if line_match:
                slot = line_match.group(1)
                break

        # IF a slot was found, telnet to the card and run a few commands
        # to insure the telnet did occur sucessfully
        if slot:

            # Get into linux mode prior to telnet to the DPC card
            conn_obj.linux_mode()
            conn_obj.tel_card_cpu(slot, 0)

            # Check the prompt mode of the connection to the DPC card
            self.assertTrue("card" in conn_obj.prompt_mode)

            # Run a command and check the output to validate the connection
            cmd_out = conn_obj.run_command("ls /sys/class/net/mcdma{0}".format(slot))
            self.assertTrue("No such file or directory" not in cmd_out)

            conn_obj.exit_tel()

        # Go back to boxer mode on the active MIO
        conn_obj.cli_mode()

        # Check if we can enter config mode
        conn_obj.config_mode()

        # Run a command and check the command output to insure it ran properly
        cmd_output = conn_obj.run_command("clock timezone")
        self.assertTrue("Incomplete command" in cmd_output)
        self.assertTrue(conn_obj.prompt_mode == "config")

        # Exit config mode   and check the mode of the connection
        conn_obj.exit_config_mode()
        self.assertTrue(conn_obj.mode == "boxer")

        # Check that we can enter unit test mode
        conn_obj.unit_test_mode()

        # Run a unittest command   and check the output
        cmd_output = conn_obj.run_command("show config rct")
        self.assertTrue("Unittest Type" in cmd_output)
        self.assertTrue(conn_obj.prompt_mode == "unittest")

        # Exit unittest mode   and check if we are in the boxer mode
        conn_obj.exit_unit_test_mode()
        self.assertTrue(conn_obj.mode == "boxer")

        # Now test the system test mode
        conn_obj.system_test_mode()

        # Run a command
        cmd_output = conn_obj.run_command("show control-plane-test counters")
        self.assertTrue("Control plane defect tests from the primary" in cmd_output)
        self.assertTrue(conn_obj.prompt_mode == "system-test")

        conn_obj.exit_system_test_mode()
        self.assertTrue(conn_obj.prompt_mode == "normal")

    def test_ssh_conn_starosdevice(self):
        """
        Test that will create a Ssh Connection to the device.  It will perform
        some tests in this one method.

        :return: None
        """

        # Get the device name. This block will use the first device in the list
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("starosdevice")

        if not len(dev_list):
            self.skipTest("List of Staros devices is empty")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Create the connection object to the device
        conn_obj = connection.StarOSDeviceConnection(con_dict)

        conn_obj.login()
        self.assertTrue(isinstance(conn_obj.isalive(), bool), "Connection is up")
        res = conn_obj.run_command("uname -a")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        res = conn_obj.run_command("df -h")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        conn_obj.logout()
        self.assertFalse(conn_obj.isalive(), "Connection is alive,")

    def test_ssh_conn_starosdevice_alive(self):
        """
        Test that will check a Ssh Connection to the device is alive.

        :return: None
        """

        # Get the device name. This block will use the first device in the list
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("starosdevice")
        if not len(dev_list):
            self.skipTest("List of Staros devices is empty")
        dev_name = dev_list[0]

        # Get the connection dict
        con_dict = yaml_obj.get_connection_dict(dev_name)

        # Create the connection object to the device
        conn_obj = connection.StarOSDeviceConnection(con_dict)
        conn_obj.login()
        self.assertTrue(conn_obj.isalive(), "Connection is not alive")
        conn_obj.logout()
        self.assertFalse(conn_obj.isalive(), "Connection is alive")


if __name__ == "__main__":


