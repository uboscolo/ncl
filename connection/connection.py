""" Module containing a generic Connection object.
This object is used to handle various types of connections like telnet and ssh
Generic APIs to open, close and execute commands over connections are
offered in this module
The device arguments is a dictionary that reflects the testbed yaml devices
structure, some elements of which are described below:

# devices block
# -------------
#   all testbed devices are described here
devices:

    <name>: # device name (hostname) goes here. each device requires its
            # own description section within devices block

        type:   # device type generic string
                # use this to describe the type of device
                #   Eg: ASR9k

        connections:
            # block describing the 'ways' or 'methods' of connecting
            # to this testbed device. eg, telnet, ssh, netconf, etc
            # (required)

            <a/b/alt>:
                # traditional Csccon style connection naming convention
                # describing console connection A/B and the alt (mgmt)
                # connection
                # (optional)
                protocol:   # connection protocol, eg, telnet/ssh
                            # (required)
                ip:     # device hostname or connection ip address
                        # (required)
                port:   # port to connect to
                        # (optional)
                class:  # connection class to use. use this field to
                        # provide an alternative connection class to use
                        # to connect to this connection
                        # (default: ats.connection.bases.Csccon)
                        # (optional)

            <name>:
                # new - any other connection methods/ways to talk to this
                # testbed device. must specify connection class, as the
                # infrastructure cannot guess how to connect to this new
                # description
                # (optional)
                protocol:   # connection protocol
                            # (optional)
                ip:     # device hostname or connection ip address
                        # (optional)
                class:  # connection class to use. use this field to
                        # provide an alternative connection class to use
                        # to connect to this connection
                        # (required)

        custom:
            # any custom key/value pairs specific to this device
            # (optional)
            <key>: <value>

Example:
"""
import logging
import libs.comms.mitg_telnet as mitg_telnet
import libs.comms.mitg_ssh as mitg_ssh
import libs.eng_mibu_exceptions as eme

logger = logging.getLogger(__name__)


class ConnectionMixin:
    """ This class implements teh common methods that are applicable to the
    connection classes in this module

    """

    def __init__(self, connection):
        """
        Init method

        :param connection: connection object, ssh or telnet
        """

        self.connection = connection

    def login(self, timeout=60):
        """
        login method.  This will call the low-level login method
        The low level connection object is contained in the connection parameter.

        :param int timeout: Timeout to log into the device

        :return: Return anything returned from the low level login method

        """
        self.connection.login(timeout=timeout)

    def logout(self):
        """
        logout method.  This will call the low-level logout method
        The low level connection object is contained in the connection parameter.

        :return: Return anything returned from the low level logout method

        :Examples:
        """
        return self.connection.logout()

    def reconnect(self, attempts=5, sleep_time=5, timeout=60):
        """
        Reconnect method.  This will call the low-level connection reconnect method.
        The low level connection object is contained in the connection parameter.

        :param int attempts: number of attempts
        :param int sleep_time: time to sleep before attempts
        :param int timeout: Timeout value to re-login

        :return: None

        :Examples:
        """

        # Call low level reconnect method and insure the connection is in priveledged mode
        self.connection.reconnect(attempts=attempts, sleep_time=sleep_time, timeout=timeout)

    def set_prompt(self, prompt):
        """
        This function will call the low level connection set_prompt method.

        :param str/list prompt: Update the current prompt string for the object
        :return: what is returned from the set_prompt method of the low level set_prompt

        **Example**

        """
        return self.connection.set_prompt(prompt)

    def add_prompt(self, prompt):
        """
        This function will call the low level connection add_prompt method

        :param str|list prompt: Extend the current prompt string for the object
        :return: Return of the low level add_prompt
        :raises eme.EngProcCmd: If method is called with invalid connection type

        **Example**

        .. note:: This will change the prompt for the connection.  Commands run after
        this call will use the NEW prompt

        """
        return self.connection.add_prompt(prompt)

    def run_command(self, command, prompt_str=None, timeout=120, wait_for_prompt=True):
        """
        This method will call the low level run_command method depending on the
        connection.  The return of the low level method is returned to the caller.

        :param str command: Command to run.
        :param str prompt_str: This is the prompt string to use for the command.
                               If one is not passed in then the method will use the current prompt string.
                               This is used to override the current prompt string
        :param int timeout: Timeout in seconds to wait for the command to complete. Default is 10
        :param bool wait_for_prompt: Default is True, if we need to wait for the prompt

        :return: Returns the output from the command returned by the Host
        :rtype: str

        **Example**

        """
        try:
            ret = self.connection.run_command(command, prompt_str, timeout, wait_for_prompt)
        except (eme.EngTimeoutError, TimeoutError, EOFError) as err:
            logger.warning("Command timed out ({0}), reconnecting ...".format(err))
            self.reconnect(attempts=3, timeout=timeout)
            # raise to the upper layer to signal a timeout occurred
            raise eme.EngConnectionError("Timeout: {}".format(err))

        return ret

    def execute_command(self, command, prompt_str=None, timeout=120, check_errors=True):
        """Calls the low level connection execute_command method

        :param str command: Command string
        :param str prompt_str: Prompt string to be used for this command.  Overrides the one to the connection
        :param int timeout: Timeout to wait for the command to comlete
        :param bool check_errors: Check for errors

        :return: Command output
        :rtype: str

        **Example**

        """
        try:
            ret = self.connection.execute_command(command, prompt_str, timeout, check_errors)
        except (eme.EngTimeoutError, TimeoutError, EOFError) as err:
            logger.warning("Connection error with reason - ({0}), reconnecting ...".format(err))
            self.reconnect(attempts=3, timeout=timeout)
            # raise to the upper layer to signal a timeout occurred
            raise eme.EngConnectionError("Timeout: {}".format(err))

        return ret

    def isalive(self):
        """
        Method to check the connection status.

        :return: True when connection is up
        :rtype: bool
        """
        return self.connection.isalive()


class MitgConnection(ConnectionMixin):
    """Mitg Connection class.  This is the base class for MITG devices.  This class
    is used for common MITG devices.

    Mitg Connection object class to inherit from. Every Mitg Connection
    object should inherit from this class

    """

    def __init__(self, conn_info_dict):
        """
        Init method

        :param dict conn_info_dict: Connection Dictionary

        :return Connection
        :rtype: MitgConnection
        :raises eme.EngProcCmd: Boxer or linux prompt not specified.  More than 1 device in Dict
        :raises eme.EngProcCmd: Host not specified.  User name or password not specified

        """
        self.cli_prompt = None
        self.linux_prompt = None
        self._mitg_generic_prompt = '[local]'
        self.mode = 'boxer'
        self.prompt_mode = 'normal'
        self.card_prompt = [None]
        self.card_list = []

        self.cli_prompt = conn_info_dict['prompt']
        self.linux_prompt = conn_info_dict['linux_prompt']
        if not self.cli_prompt or not self.linux_prompt:
            raise eme.EngProcCmd("Either boxer or linux prompt not specified ({0}, {1})".format(self.cli_prompt,
                                                                                                self.linux_prompt))
        # Extract the host_name & protocol
        self.host_name = conn_info_dict['host']
        self.system_hostname = conn_info_dict['system_hostname']
        self.protocol = conn_info_dict['proto']
        ts_port = conn_info_dict['ts_port']

        if not self.host_name:
            raise eme.EngProcCmd("Ip (host_name) not specified ({0})".format(self.host_name))

        self.user_name = conn_info_dict['user_name']
        self.password = conn_info_dict['password']
        self.prompt = conn_info_dict['prompt']

        if not self.user_name or not self.password:
            raise eme.EngProcCmd("User name or password not specified ({0}, {1})".format(self.user_name, self.password))

        self.state = "Idle"

        # Check that the caller specifies the protocol of the connection
        if not self.protocol:
            raise eme.EngProcCmd("Error: Creating a connection without specifying protocol type")

        # Create a connection using the parameters specified in the connection
        # dictionary.  One parameter is the protocol.  Currently the only 2 valid
        # protocols is ssh and telnet.
        # If the caller specifies the term server port.  Pass this info to the
        # low level connection object in the option parameters
        options = {}
        if ts_port:
            options['ts_port'] = ts_port

        if self.protocol == "ssh":
            connection = mitg_ssh.SshController(conn_info_dict["host"],
                                                conn_info_dict["user_name"],
                                                conn_info_dict["password"],
                                                conn_info_dict["prompt"],
                                                **options)
        elif self.protocol == "telnet":
            # Create a telnet connection
            connection = mitg_telnet.TelnetController(conn_info_dict['host'],
                                                      conn_info_dict['user_name'],
                                                      conn_info_dict['password'],
                                                      conn_info_dict['prompt'])
        else:
            raise eme.EngProcCmd("invalid protocol type:  {0})".format(self.protocol))

        super().__init__(connection)

    def get_protocol(self):
        """
        Method to get the low-level protocol (i.e. Telnet or SSH)

        :return: str Telnet OR SSH
        :rtype: str

        """
        return self.protocol

    def cli_mode(self):
        """
        This method should be run on MITG devices on the management cards.  This will
        change the connection state to the Boxer mode.

        :return: None

        .. note:: This command will change the mode to Boxer.

        """
        if self.mode == "boxer" and self.prompt_mode == "normal":
            return
        self.set_prompt(self.cli_prompt)
        self.prompt_mode = "normal"
        self.mode = 'boxer'
        self.execute_command("exit")

    def reconnect(self, attempts=240, sleep_time=5, timeout=30):
        """
        Reconnect method.  This will call the low-level connection reconnect method.
        The low level connection object is contained in the connection parameter.

        :param int attempts: number of attempts
        :param int sleep_time: time to sleep before attempts
        :param int timeout: Timeout value to reconnect

        :return: None

        :Examples:
        """

        # Make sure the prompt and prompt state are initialized correctly
        self.prompt_mode = "normal"
        self.set_prompt(self.cli_prompt)

        # Call low level reconnect method and insure the connection is in priveledged mode
        self.connection.reconnect(attempts=attempts, sleep_time=sleep_time, timeout=timeout)
        self.enable_priv_mode()

    def login(self, timeout=60):
        """
        login method.  This will call the low-level login method
        The low level connection object is contained in the connection parameter.

        :param int timeout: Timeout to log into the device

        :return: Return anything returned from the low level login method

        :Examples:
        """
        success = False
        try:
            self.connection.login(timeout)
            success = True
        except (eme.EngConnectionError, eme.EngTelnetError, eme.EngTimeoutError) as err:
            logger.info("Unable to login: {}".format(err))

        if not success:
            # Add the mitg generic prompt, and try again, if successful
            # The generic prompt will be removed after the system hostname is set
            curr_promptlist = self.connection.get_promptlist()
            new_promplist = curr_promptlist.copy()
            new_promplist.append(self._mitg_generic_prompt)
            self.connection.set_prompt(new_promplist)
            try:
                self.connection.login(timeout)
            except (eme.EngConnectionError, eme.EngTelnetError, eme.EngTimeoutError) as err:
                # Reset prompt
                self.set_prompt(curr_promptlist)
                raise eme.EngConnectionError("Failed to login with generic prompt: {}".format(err))

            # We are in with after adding the generic prompt, now adding the hostname
            logger.info("System hostname will be set to {}".format(self.system_hostname))
            self.set_prompt('(config)#')
            self.run_command('config')
            self.run_command("system hostname {}".format(self.system_hostname))
            # Reset the prompt and exit
            self.set_prompt(curr_promptlist)
            self.run_command('exit')

        return

    def enable_priv_mode(self):
        """
        Method to enable priviledged mode in the boxer cli

        :return: None
        """
        if self.mode != "boxer":
            self.cli_mode()
        self.execute_command("cli test-commands password boxer")

    def linux_mode(self, in_shell=False):
        """
        This method should be run on MITG devices on the management cards.  These
        cards can be in linux or boxer mode.  This method will change the mode
        of the connection to Linux.

        """

        self.set_prompt(self.linux_prompt)
        # Check to see if the mode is already Linux
        if self.mode == "linux":
            return
        self.prompt_mode = "normal"
        self.mode = 'linux'
        if not in_shell:
            self.execute_command("debug shell")

    @staticmethod
    def _linux_prompt(card_slot, cpu_number):
        """
        Method that will return the prompt string for the Linux prompt for an MITG device.
        :param int card_slot: Card Slot   1-based
        :param int cpu_number: CPU Number 0-based

        :return: Linux prompt string
        :rtype: str
        """

        prompt = ':card{0}-cpu{1}#'.format(card_slot, cpu_number)
        return prompt

    def tel_card_cpu(self, card_slot, cpu_number, timeout=10):
        """
        Method to telnet to another CPU within the chassis.  The caller will
        specify the slot and cpu.  The method will perform the work to connect
        to the specified CPU device.

        :param int card_slot: Card Slot   1-based
        :param int cpu_number: Cpu Number 0-based
        :param int timeout: Timeout value.  Amount of time in seconds to wait for prompt

        :return: Output of the command
        :rtype: str
        :raises eme.EngProcCmd: If the current mode of the connection is not linux

        """
        if self.mode != 'linux':
            raise eme.EngProcCmd("Error: Attempting to Telnet when not in Linux mode {0}".format(self.mode))
        # Store off the old Prompt
        self.card_prompt.append(self.prompt)
        self.prompt_mode = "card{0}_{1}".format(card_slot, cpu_number)
        self.set_prompt(self._linux_prompt(card_slot, cpu_number))
        logger.debug('Telnet to Card {0} CPU {1}, TO:{2}'.format(card_slot, cpu_number, timeout))
        cmd_out = self.run_command('telnet card{0}-cpu{1}'.format(card_slot, cpu_number), timeout=timeout)
        self.card_list.append([card_slot, cpu_number])
        return cmd_out

    def exit_tel(self):
        """
        Method to exit the telnet connection.  This is typically run after the script telnets
        to another card/cpu.  This method will exit this telnet, which will cause the connection
        to return to the preious cpu device.

        :return: output from exit command
        :rtype: str

        :Examples:

        """
        (card_slot, cpu_number) = self.card_list.pop()
        logger.info("Exit Telnet From Card:{0} CPU:{1}".format(card_slot, cpu_number))
        if len(self.card_list):
            # Let's jump back
            self.set_prompt(self._linux_prompt(self.card_list[-1][0], self.card_list[-1][1]))
            self.prompt_mode = "card{0}_{1}".format(self.card_list[-1][0], self.card_list[-1][1])
        else:
            # This is where we started from, it has to be linux
            self.set_prompt(self.linux_prompt)
            self.prompt_mode = "linux"
        self.run_command("exit")

    def config_mode(self):
        """
        Method to enter config mode from boxer mode.

        :return: Output from entering config mode
        :rtype: str

        """
        self.cli_mode()
        # Set the Mode to Config
        self.prompt_mode = "config"
        conf_prompt = self.cli_prompt.replace('#', '') + '(config)#'
        self.set_prompt(conf_prompt)
        return self.execute_command("conf")

    def exit_config_mode(self):
        """
        Method to exit config mode.

        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd:  If the method was run when not in config mode
        """
        if self.prompt_mode != "config":
            raise eme.EngProcCmd(
                "Error: Attempt to exit Config mode when not in Config Mode: {0}".format(self.prompt_mode))
        self.cli_mode()

    def context_mode(self, context):
        """
        Method to enter context mode from boxer mode.

        :param context: Name of the context to switch to
        :return: Output from entering context mode
        :rtype: str

        """
        self.cli_mode()
        # Set the Mode to Config

        self.prompt_mode = "context"
        context_prompt = self.cli_prompt.replace('local', context)
        self.set_prompt(context_prompt)
        return self.execute_command("context {0}".format(context))

    def exit_context_mode(self, context):
        """
        Method to exit config mode.

        :param: Name of the context to exit from and return to local
        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd:  If the method was run when not in config mode
        """
        if self.prompt_mode != "context":
            raise eme.EngProcCmd("Error: Attempt to exit Context mode for {0} "
                                 "when not in Context Mode: {1}".format(context, self.prompt_mode))
        # self.context_mode(context='local')
        self.prompt_mode = "normal"
        self.set_prompt(self.cli_prompt)
        self.execute_command('context local')
        # self.cli_mode()

    # Following Block puts the MIO into unittest mode
    def unit_test_mode(self):
        """
        Method to enter unit test mode from boxer.  The session needs to be in Linux
        mode prior to calling this function.

        :return: Output from the unittest command
        :rtype: str
        :raises eme.EngProcCmd: Running this command when the mode is not in the normal boxer mode

        """
        self.cli_mode()
        if self.prompt_mode != "normal":
            raise eme.EngProcCmd("Error: Attempted to enter unittest mode "
                                 "but not in boxer mode: {0}".format(self.prompt_mode))
        self.prompt_mode = "unittest"
        new_prompt = self.cli_prompt.replace('#', '') + '(unittest)#'
        self.set_prompt(new_prompt)
        cmd_out = self.execute_command("unittest")
        logger.debug("Command Out: {0}".format(cmd_out))
        return cmd_out

    # Following Block exits the Exit Unit Test mode
    def exit_unit_test_mode(self):
        """
        Method to exit unit test mode.  The session needs to be in Boxer
        Unittest Mode prior to calling this function

        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd: If not in unit test mode when method was run

        """
        if self.prompt_mode != "unittest":
            raise eme.EngProcCmd(
                "Error: Attempting to exit Unittest when not in Unittest mode Mode:{0}".format(self.prompt_mode))
        if self.mode != "boxer":
            raise eme.EngProcCmd("Error: Attempting to exit Unittest when not in boxer mode Mode:{0}".format(self.mode))
        self.prompt_mode = "normal"
        self.set_prompt(self.cli_prompt)
        cmd_out = self.execute_command("exit")
        logger.debug("Command Out: {0}".format(cmd_out))
        return cmd_out

    def system_test_mode(self):
        """
        Method to enter system-test mode from boxer.  The session needs to be in Linux
        mode prior to calling this function.

        :return: Output from the system-test command
        :rtype: str
        :raises eme.EngProcCmd: Running this command when the mode is not in the normal boxer mode

        """
        self.cli_mode()
        if self.prompt_mode != "normal":
            raise eme.EngProcCmd(
                "Error: Attempted to enter system-test mode   but not in boxer mode: {0}".format(self.prompt_mode))
        self.prompt_mode = "system-test"
        new_prompt = self.cli_prompt.replace('#', '') + '(system-test)#'
        self.set_prompt(new_prompt)
        cmd_out = self.execute_command("system-test")
        logger.debug("Command Out: {0}".format(cmd_out))
        return cmd_out

    def exit_system_test_mode(self):
        """
        Method to exit system-test mode.  The session needs to be in Boxer
        Sytem-test Mode prior to calling this function

        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd: If not in system-test mode when method was run

        """
        if self.prompt_mode != "system-test":
            raise eme.EngProcCmd("Error: Attempting to exit system-test "
                                 "when not in system-test mode Mode:{0}".format(self.prompt_mode))
        if self.mode != "boxer":
            raise eme.EngProcCmd("Error: Attempting to exit system-test "
                                 "when not in boxer mode Mode:{0}".format(self.mode))
        self.prompt_mode = "normal"
        self.set_prompt(self.cli_prompt)
        cmd_out = self.execute_command("exit")
        logger.debug("Command Out: {0}".format(cmd_out))
        return cmd_out


class ASR5500Connection(MitgConnection):
    """ASR5500 Connection class.  This is the sub class that gets created when
    the connection is to an ASR5500 device.

    ASR5500 Connection object class

    """

    def __init__(self, conn_info_dict):
        """
        Init method for the ASR5500 connection object.

        :param dict conn_info_dict: Dictionary of the connection of the device.  See example above

        :return: Connection object
        :rtype: ASR5500Connection
        :raises eng.EngProcCmd

        """

        super().__init__(conn_info_dict)
        self.__expand_linux_prompt()

    def __expand_linux_prompt(self):
        """Private Method to extend prompt to card5 and card6 in ASR5500
        """
        if "card5" in self.linux_prompt:
            prompt_list = [self.linux_prompt, self.linux_prompt.replace("5", "6")]
        elif "card6" in self.linux_prompt:
            prompt_list = [self.linux_prompt.replace("6", "5"), self.linux_prompt]
        else:
            prompt_list = self.linux_prompt
        self.linux_prompt = prompt_list

    # Following Block contains support for AFIO CLI
    def afio_mode(self):
        """
        Method to enter AFIO mode.  This is the fabric mode.  The session needs to be in Linux
        Mode prior to calling this function

        :return: output from the afio command
        :rtype: str
        :raises eme.EngProcCmd: If connection mode is not in linux when command is run

        :Examples:
        """
        if self.mode != "linux":
            raise eme.EngProcCmd("Error: Attempting to Go into AFIO mode not from linux mode:{0}".format(self.mode))
        self.prompt_mode = "afio"
        self.set_prompt('[AFCLI] afio:')
        cmd_out = self.execute_command("afio")
        logger.info("Command Out: {0}".format(cmd_out))
        return cmd_out

    def exit_afio_mode(self):
        """
        Method to exit AFIO mode.  The session needs to be in AFIO
        Mode prior to calling this function

        :return: Output from the exit command
        :rtype: str

        """
        if self.prompt_mode != "afio":
            raise eme.EngProcCmd("Error: Attempting to Exit AFIO mode not from AFIO mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "normal"
        self.set_prompt(self.linux_prompt)
        logger.info("Leaving Afio Mode")
        self.execute_command("exit")

    def petra_mode(self, dev_number):
        """
        Method to enter Petra Mode.  The user needs to provide the Petra device

        :param int dev_number: Petra Device ID

        :return: None
        :raises eme.EngProcCmd: If mode was not in linux when command was run

        """
        if self.mode != "linux":
            raise eme.EngProcCmd("Error: Attempting to Go into Petra mode not from linux mode:{0}".format(self.mode))
        self.prompt_mode = "petra"
        self.set_prompt('petra-b.*:')
        self.execute_command('petra-b system-device-id {0}'.format(dev_number))
        logger.info("Going into Petra Mode")

    def exit_petra_mode(self):
        """
        Method to exit Petra Mode.  This command should only be run when the connection is
        in Petra Mode.

        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd: If connection mode was not Petra Mode

        """
        if self.prompt_mode != "petra":
            raise eme.EngProcCmd("Error: Attempting to Exit Petra mode "
                                 "not from Petra mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "afio"
        self.set_prompt('[AFIO-D.*] afio.*:')
        self.execute_command("exit")
        logger.info("Leaving petra_mode")

    def arad_mode(self, dev_number):
        """
        Method to enter Arad Mode.  This command should only be run when the connection is
        in linux Mode.

        :param int dev_number: Arad device ID

        :return: None
        :raises eme.EngProcCmd: If mode is not afio mode

        """
        if self.prompt_mode != "afio":
            raise eme.EngProcCmd("Error: Attempting to Go into ARAD mode "
                                 "not from AFIO mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "arad"
        self.set_prompt('[AFIO-D.*] arad.*:')
        logger.debug("Device ID is {0}".format(dev_number))
        self.execute_command('arad system-device-id {0}'.format(dev_number))
        logger.debug("Going into Arad Mode")

    def exit_arad_mode(self):
        """
        Method to exit Arad Mode.  This command should only be run when the connection is
        in Arad Mode.

        :return: None
        :raises eme.EngProcCmd: If mode is not Arad mode

        """
        if self.prompt_mode != "arad":
            raise eme.EngProcCmd("Error: Attempting to Exit ARAD mode "
                                 "not from Arad mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "afio"
        self.set_prompt('[AFIO-D.*] afio.*:')
        self.execute_command("exit")
        logger.debug("Leaving arad_mode")

    def fe600_mode(self, dev_number):
        """
        Method to enter FE600 Mode.  The FE600s are Broadcom fabric switch devices.  This command should
        only be run in afio mode.

        :param int dev_number: FE600 device ID

        :return: Output from the fe600 command
        :rtype: str
        :raises eme.EngProcCmd: If the connection mode was not afio

        """
        if self.prompt_mode != "afio":
            raise eme.EngProcCmd("Error: Attempting to Go into ARAD mode "
                                 "not from AFIO mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "fe600"
        self.set_prompt('[AFIO-D.*] fe600.*:')
        cmd_out = self.execute_command('fe600 system-device-id {0}'.format(dev_number))
        logger.debug("Going into fe600_mode")
        return cmd_out

    def exit_fe600_mode(self):
        """
        Method to exit FE600 Mode.  The FE600s are Broadcom fabric switch devices.  This command should
        only be run in fe600 mode.

        :return: None
        :raises eme.EngProcCmd: If mode was not fe600

        """
        if self.prompt_mode != "fe600":
            raise eme.EngProcCmd("Error: Attempting to Exit FE600 mode "
                                 "not from FE600 mode:{0}".format(self.prompt_mode))
        self.prompt_mode = "afio"
        self.set_prompt('[AFIO-D.*] afio.*:')
        self.execute_command("exit")
        logger.debug("Leaving fe600_mode")


class StarOSDeviceConnection(ConnectionMixin):
    """StarOs Device Connection class.  This is the sub class that gets created when
    the connection is to an StarOs device.

    StarOs device Connection object class
    """

    def __init__(self, conn_info_dict):
        """
        Init method

        :param dict conn_info_dict: Connection Dictionary

        :return Connection
        :rtype: StarOSDeviceConnection

        """
        connection = mitg_ssh.SshController(conn_info_dict["host"],
                                            conn_info_dict["user_name"],
                                            conn_info_dict["password"],
                                            conn_info_dict["prompt"])
        super().__init__(connection)

        self.host_name = conn_info_dict["host"]
        self.cimc_prompt = conn_info_dict["prompt"]
        self.prompt_mode = 'normal'

    def reconnect(self, attempts=5, sleep_time=5, timeout=60):
        """
        Reconnect method.  This will call the low-level connection reconnect method.
        The low level connection object is contained in the connection parameter.

        :param int attempts: number of attempts
        :param int sleep_time: time to sleep before attempts
        :param int timeout: Timeout value to re-login

        :return: None

        :Examples:
        """

        # Call low level reconnect method and insure the connection is in priveledged mode
        super().reconnect(attempts=attempts,
                          sleep_time=sleep_time,
                          timeout=timeout)
        self.enable_root()

    def enable_root(self):
        """
        Method to enable root, unless already root.

        :return: True when connection is up
        :rtype: bool
        """
        if self.connection.user_name == 'root':
            return

        root_prompt = []
        for prompt in self.connection.prompt_list:
            new_prompt = prompt.replace('$', '#')
            root_prompt.append(new_prompt)

        # set su -
        self.connection.set_prompt(root_prompt)
        self.connection.run_command("sudo su -")

    def cimc_chassis_mode(self):
        """
        Method to enter chassis mode from normal mode.

        :return: Output from entering chassis mode
        :rtype: str

        """
        # self.cli_mode()
        # Set the Mode to chassis

        self.prompt_mode = 'chassis'
        chassis_scope_prompt = self.cimc_prompt.replace('#', ' /chassis #')
        self.set_prompt(chassis_scope_prompt)
        return self.run_command("scope chassis")

    def exit_chassis_mode(self):
        """
        Method to exit config mode.

        :param: Name of the context to exit from and return to local
        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd:  If the method was run when not in config mode
        """
        if self.prompt_mode != "chassis":
            raise eme.EngProcCmd(
                "Error: Attempt to exit Chassis mode when not in Chassis Mode: {0}".format(self.prompt_mode))
        # self.context_mode(context='local')
        self.prompt_mode = "normal"
        self.set_prompt(self.cimc_prompt)
        self.run_command('exit', wait_for_prompt=False, timeout=10)
        # self.cli_mode()


class NexusDeviceConnection(ConnectionMixin):
    """Nexus Device Connection class.  This is the sub class that gets created when
    the connection is to a Nexus device.

    Nexus device Connection object class
    """

    def __init__(self, conn_info_dict):
        """
        Init method

        :param dict conn_info_dict: Connection Dictionary

        :return Connection
        :rtype: NexusDeviceConnection

        """
        connection = mitg_ssh.SshController(conn_info_dict["host"],
                                            conn_info_dict["user_name"],
                                            conn_info_dict["password"],
                                            conn_info_dict["prompt"])
        super().__init__(connection)

        self.host_name = conn_info_dict["host"]
        self.nexus_prompt = conn_info_dict["prompt"]
        self.prompt = self.connection.prompt_list
        self.prompt_mode = 'normal'
        self.mode = 'nexus'

        self.config_prompt = r'(config)#'
        self.if_prompt = r'(config-if)#'

        self.prompt_list = []
        self.prompt_list.append(self.nexus_prompt)
        self.prompt_dict = dict(normal=self.nexus_prompt,
                                config=self.config_prompt,
                                interface=self.if_prompt)

    def cli_mode(self):
        """
        This will change to connection to normal cli mode.

        :return: None

        """
        conn = self.connection

        if self.mode == "nexus" and self.prompt_mode == "normal":
            return

        self.set_prompt(self.nexus_prompt)
        self.prompt_mode = "normal"
        self.mode = 'nexus'
        self.run_command("end")
        logger.debug('{} {} {}'.format(self.mode, self.prompt_mode, self.nexus_prompt))

    def config_mode(self):
        """
        Method to enter config mode from normal mode.

        :return: Output from entering config mode
        :rtype: str

        """

        conn = self.connection

        # Set the Mode to config

        if self.mode == 'nexus config' and self.prompt_mode == 'config':
            return

        self.mode = 'nexus config'
        self.prompt_mode = 'config'
        self.set_prompt(self.config_prompt)

        self.run_command("config")
        logger.debug('{} {} {}'.format(self.mode,
                                       self.prompt_mode,
                                       self.connection.prompt_list))

    def config_interface_mode(self, interface):
        """
        Method to enter config mode from normal mode.

        :return: Output from entering config mode
        :rtype: str

        """

        conn = self.connection

        # Set the Mode to interface config

        self.config_mode()

        self.mode = 'nexus interface config'
        self.prompt_mode = 'interface'
        self.set_prompt(self.if_prompt)
        cmd = 'interface {}'.format(interface)
        self.run_command(cmd)

    def exit_config_mode(self):
        """
        Method to exit config mode.

        :return: <DESC>
        :rtype: str
        :raises eme.EngProcCmd:  If the method was run when not in config mode
        """
        if self.prompt_mode != "config" or self.prompt_mode != 'interface':
            raise eme.EngProcCmd(
                "Error: Attempt to exit Nexus Config mode when not in config Mode: {0}".format(self.prompt_mode))

        self.cli_mode()
        return self.run_command('end')

