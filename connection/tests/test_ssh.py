""" Module containing the unittest test cases for the connection module.
"""

import re
import libs.comms.mitg_ssh as mitg_ssh
import libs.parametrize as parametrize
import libs.mitg_yaml as mitg_yaml
import libs.eng_mibu_exceptions as eme
import unittest


class MitgSshTestCases(parametrize.ParametrizedTestCase):
    """ Unit test cases object
    """
    def setUp(self):
        """Called at the start of the test.  This method will deterine if the script
        was run as main or not.  If it is not run as main  then it will check if an
        Env. variable is set   so that is can ID the YAML file.  It will also start
        a logger.
        """
        super().setUp()

    def get_master_mio_slot(self):
        """Method to get the master MIO slot number.  For the ASR5500 platform this
        number is either 5 or 6
        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'])
        self.assertTrue(isinstance(conn, mitg_ssh.SshController))
        conn.login()
        res = conn.run_command("show card table")
        for line in res.splitlines():
            match_obj = re.search(r'([\d+]): MMIO.*Active', line)
            if match_obj:
                conn.logout()
                master = int(match_obj.group(1))
                return master
        conn.logout()
        raise RuntimeError("Was not able to find master of the chassis")

    def test_create_ssh_connection_to_server(self):
        """
        It will establish an ssh connection and then run the show version command and logout

        """

        # Get the Connection Dictionary   with the device type starosdevice
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("starosdevice")
        if not dev_list:
            return unittest.skip("no staros device in yaml")

        dev_name = dev_list[0]

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'])

        self.assertTrue(isinstance(conn, mitg_ssh.SshController))
        conn.login()
        res = conn.run_command("ls -al")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        res = conn.run_command("df -h")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        conn.logout()

    def test_create_ssh_connection1(self):
        """
        It will establish an ssh connection and then run the show version command and logout

        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'])

        self.assertTrue(isinstance(conn, mitg_ssh.SshController))
        conn.login()
        res = conn.run_command("show version")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        conn.logout()

    def test_create_ssh_connection2(self):
        """
        It will establish an ssh connection through a terminal server and run show version

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the master slot of the chassis
        master = self.get_master_mio_slot()

        if master == 5:
            master_conn_name = "cli5"
            stby_conn_name = "cli6"
        elif master == 6:
            master_conn_name = "cli6"
            stby_conn_name = "cli5"
        else:
            raise RuntimeError("Invalid master slot number {0}, "
                               "was not able to find master of the chassis".format(master))

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name, stby_conn_name)

        options = {'ts_port': conn_dict['ts_port']}
        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'], **options)

        self.assertTrue(isinstance(conn, mitg_ssh.SshController))

        # Attempt to log into the device to the standby MIO.  This should raise an exception
        with self.assertRaisesRegex(eme.EngConnectionError, "Connection is to the standby MIO:.*") as context:
            self.assertIsNotNone(context)
            conn.login(timeout=10)
        conn.logout()

        # Now attempt to log into the active MIO
        conn_dict = yaml_obj.get_connection_dict(dev_name, master_conn_name)
        options = {'ts_port': conn_dict['ts_port']}
        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'], **options)

        conn.login(timeout=10)
        res = conn.run_command("show version")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        conn.logout()

    def test_create_ssh_connection3(self):
        """
        It will establish an ssh connection and then run the show diameter peers full all command and logout

        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                      conn_dict['password'], conn_dict['prompt'])

        self.assertTrue(isinstance(conn, mitg_ssh.SshController))
        conn.login()
        res = conn.run_command("show diameter peers full all")
        self.assertTrue(isinstance(res, str), "Incorrect type for res: {0}".format(type(res)))
        conn.logout()

    def test_ssh_flush_connection(self):
        """
        It will establish an ssh connection and then run a command after logging into the device.
        It will check the output of the command.  It will then send a few commands and not wait
        for the prompt.  This should creat a command offset  but the test will run the flush
        command and then run another command to make sure the flush worked.
        """

        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        ssh_conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                          conn_dict['password'], conn_dict['prompt'])
        self.assertTrue(isinstance(ssh_conn, mitg_ssh.SshController))
        ssh_conn.login()

        # Now run a command and check the output
        found_line = False
        res = ssh_conn.run_command("show version")
        for line in res.splitlines():
            if re.search(r'Image Version:', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line)

        # Now that we are logged into the chassis, send mulitple commands to
        # create an out of sync issue.  The flush command should remove this output
        res = ssh_conn.connection_id.sendline("show temperature")
        self.assertTrue(isinstance(res, int), "Incorrect type for res: {0}".format(type(res)))
        res = ssh_conn.connection_id.sendline("show ntp status")
        self.assertTrue(isinstance(res, int), "Incorrect type for res: {0}".format(type(res)))

        # Now flush the connection
        ssh_conn.conn_flush()

        # Now run a command and check the output
        res = ssh_conn.run_command("show version")
        for line in res.splitlines():
            if re.search(r'Image Version:', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line, msg="Error checking command after flush")

        ssh_conn.logout()

    def test_ssh_ts_flush_connection(self):
        """
        It will establish an ssh connection and then run the show diameter peers full all command and logout

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the master slot of the chassis
        master = self.get_master_mio_slot()

        if master == 5:
            master_conn_name = "cli5"
        elif master == 6:
            master_conn_name = "cli6"
        else:
            raise RuntimeError("Invalid master slot number {0}, w"
                               "as not able to find master of the chassis".format(master))

        # Get the connection params
        conn_dict = yaml_obj.get_connection_dict(dev_name)

        # If the ts_port is not None   then add it to the options
        if conn_dict['ts_port']:
            options = {'ts_port': conn_dict['ts_port']}

        # Create the SSH connection
        ssh_conn = mitg_ssh.SshController(conn_dict['host'], conn_dict['user_name'],
                                          conn_dict['password'], conn_dict['prompt'])

        self.assertTrue(isinstance(ssh_conn, mitg_ssh.SshController))

        # Log into the connection
        ssh_conn.login()

        # Now run a command and check the output
        found_line = False
        res = ssh_conn.run_command("show version")
        for line in res.splitlines():
            if re.search(r'Image Version:', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line)

        # Now that we are logged into the chassis, send mulitple commands to
        # create an out of sync issue.  The flush command should remove this output
        res = ssh_conn.connection_id.sendline("show temperature")
        self.assertTrue(isinstance(res, int), "Incorrect type for res: {0}".format(type(res)))
        res = ssh_conn.connection_id.sendline("show ntp status")
        self.assertTrue(isinstance(res, int), "Incorrect type for res: {0}".format(type(res)))

        # Now flush the connection
        ssh_conn.conn_flush()

        found_line = False
        # Now run a command and check the output
        res = ssh_conn.run_command("show version")
        for line in res.splitlines():
            if re.search(r'Image Version:', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line, msg="Error checking command after flush")

        ssh_conn.logout()

    def test_ssh_ts_connection(self):
        """
        It will establish an ssh connection with a term server connection

        """
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the connections dictionary
        connections_dict = yaml_obj.get_device_connections(dev_name)

        # Init the connection name to use in test
        con_name_to_use = ""

        # Find one where the connection where there exists a ts_port key  and it is not to slot 5 or 6
        for con_name in connections_dict:
            if '5' in con_name or '6' in con_name:
                continue
            try:
                if 'ts_port' in connections_dict[con_name]:
                    con_name_to_use = con_name
                    break
            except:
                continue

        # Check if there is a connection to use
        if not con_name_to_use:
            return

        # Get the device params
        conn_dict = yaml_obj.get_connection_dict(dev_name, con_name_to_use)

        # If the ts_port is not None   then add it to the options
        options = {}
        if conn_dict['ts_port']:
            options = {'ts_port': conn_dict['ts_port']}

        # Create the SSH connection
        ssh_conn = mitg_ssh.SshController(conn_dict['host'],
                                          conn_dict['user_name'],
                                          conn_dict['password'],
                                          conn_dict['prompt'],
                                          **options)
        self.assertTrue(isinstance(ssh_conn, mitg_ssh.SshController))

        # Log into the connection
        ssh_conn.login()

        # Now run a command and check the output
        found_line = False
        res = ssh_conn.run_command("ls -l /")
        for line in res.splitlines():
            if re.search(r'boot1', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line)

        ssh_conn.logout()

    def aatest_ssh_add_prompt(self):
        """
        It will establish an ssh connection to one of the DCP cards.
        ** This needs more work.
        RAN THIS COMMAND TO MAKE IT WORK    python test_mitg_ssh.py -i ch24.yaml

        """

        # Get the YAML dictionary
        # Get the Connection Dictionary   with the device type ASR5500
        yaml_obj = mitg_yaml.Mitg_Yaml(self.param)

        # Get the device name. This block will use the first device in the list
        dev_list = yaml_obj.get_devices_by_devtype("ASR5500")
        dev_name = dev_list[0]

        # Get the device params
        (proto, host, ts_port, prompt) = yaml_obj.get_connection_params(dev_name, connection_name="slot2-cpu0")
        (user, passwd, pmpt, host, bulk, linux_prompt) = yaml_obj.get_custom_params(dev_name)

        # If the ts_port is not None   then add it to the options
        options = {}
        if ts_port:
            options = {'ts_port': ts_port}

        # Create the SSH connection
        ssh_conn = mitg_ssh.SshController(host, user, passwd, pmpt, **options)
        self.assertTrue(isinstance(ssh_conn, mitg_ssh.SshController))

        ssh_conn.set_prompt("asr5500:card9-cpu2#")
        ssh_conn.set_prompt("test_prompt11")
        ssh_conn.set_prompt("test_prompt22")

        # Check the current prompt list
        cur_prompt_list = ssh_conn.get_promptlist()

        found_first = found_2nd = False
        for prompt in cur_prompt_list:
            if re.search(r'test_prompt11', prompt):
                found_first = True
            if re.search(r'test_prompt22', prompt):
                found_2nd = True
        self.assertTrue(found_first and found_2nd)

        cur_match_list = ssh_conn.get_registered_strings()
        found_first = found_2nd = False
        for prompt in cur_match_list:
            if type(prompt) == str:
                if re.search(r'test_prompt11', prompt):
                    found_first = True
                if re.search(r'test_prompt22', prompt):
                    found_2nd = True
        self.assertTrue(found_first and found_2nd)

        ssh_conn.set_prompt("asr5500:card2-cpu0#")

        # Log into the connection
        ssh_conn.login()

        # Now run a command and check the output
        found_line = False
        res = ssh_conn.run_command("ls -l /")
        for line in res.splitlines():
            if re.search(r'hd-raid', line):
                found_line = True
                break

        # Check if line was found
        self.assertTrue(found_line)

        ssh_conn.logout()


if __name__ == "__main__":
 parametrize.parse_and_run_as_main(MitgSshTestCases, extended_class=None)
