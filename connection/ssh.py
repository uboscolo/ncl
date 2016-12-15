""" Module containing the MITG SSH Connection object.  This object is used a parent
class for MITG platforms ASR5500 and Virt.  This class is also used when using SSH
to conect to other devices like PCs etc.
"""

import logging
import re
import time
import pexpect
import libs.eng_mibu_exceptions as eme

# pylint: disable=C0103
logger = logging.getLogger(__name__)
mlog_idx = 5000

def create_esc_prompt(prompt_str):
    """
    This function will take a string and return a string with the required
    characters escapped to be used for prompt matching on the telnet connection

    :param str prompt_str: Prompt String

    :return: Prompt string with characters escaped
    :rtype: str


    .. note:: This method is hidden

    """
    return prompt_str.\
        replace('[', '\[').\
        replace(']', '\]').\
        replace('#', '\#').\
        replace('(', '\(').\
        replace(')', '\)').\
        replace('/', '\/'). \
        replace('*', '\*'). \
        replace('$', '\$')


class SshController:
    """MITG SSH class.

    Provides the default ssh connection object class to inherit from.
    This object is also used when the SW connects to non-MITG devices using
    SSH
    """

    def __init__(self, host, user_name, password, prompt, **options):
        """
        INIT method of the ssh_controller object.

        :param str host: Host name
        :param str user_name: User Name  (i.e. staradmin)
        :param str password: Password of the User used to log into the device
        :param str prompt: Prompt string
        :param array **options: Various option parameters
        :raises: eme.EngProcCmd: if password is not string
        :return: None

        :Examples:

        >>> import libs.comms.mitg_ssh
        >>> obj = SshController('host.com', 'user', 'passwd', prompt='hey#')
        >>> obj.login(40)

        """

        if not isinstance(password, str):
            raise eme.EngProcCmd("Invalid password type {0}".format(type(password)))
        self.host_name = host
        self.user_name = user_name
        self.password = password
        self.initial_prompt = prompt
        self.options = options
        # self.generic_prompt = "([^ \r\n][^\r\n]*[#>\$] ?)([\x00-\x1F]\[K)?$"
        self.ssh_options = ["UserKnownHostsFile=/dev/null", "StrictHostKeyChecking=no"] 
        self.connection_id = None
        self.results = None

        # Event reg ex string list  &  its associated method callback
        self.event_list = []
        self.callback_list = []

        # State of the connection  & protocol type
        self.state = "Idle"
        self.protocol = "SSH"

        self.num_sendline_attempts_to_login = 0  # Number of attempts to log into the chassis
        self.prompt_list = [self.initial_prompt]  # List of prompts to expect
        self.debug = False  # Debug flag.  Turns on some debug in the module

        # Create the exception reg ex strings to method mappings
        self.exc_dict = {pexpect.TIMEOUT: self._handle_timeout,
                         pexpect.EOF: self._handle_eof,
                         "Do you want to continue": self._handle_cimc_confirm}

        # Create the Login regex and function mappings
        self.login_dict = {"Are you sure you want to continue connecting \(yes/no\)\?": self._handle_new_key,
                           "([Ll]ast)? [lL]ogin:": self._handle_login,
                           "[pP]assword:": self._handle_password,
                           "Enter your option : ": self._handle_ts_option,
                           "Abort Boot by Depressing": self._handle_cfe_break,
                           "Press enter to get a login shell:": self._handle_login_shell,
                           "This console on ASR5500 card \d is inactive.": self._handle_log_sdby_mio}

    def __repr__(self):
        """
        REPR function.  This is to assist in debugging.

        :return: Object specifics to uniquely identify the connection
        :rtype: str

        :Examples:

        """
        return "SSH Connection to Host {0} state {1}".format(self.host_name, self.state)

    def _expect(self, prompt=None, t_out=120):
        """
        Expects an event and calls back the event handler if the connection is valid
        and the prompt is defined. if prompt is passed as an argument it will be used as
        the prompt for following calls within the same instance
        Notice that this function will loop until one of the callbacks - normally
        the ones that have found the prompt - return True

        :param str prompt: Optionally expected prompt
        :param int t_out: Time out in seconds for the command to complete.

        :return: self.results: Command output.
        :rtype: byte array
        :raises: eme.EncConnectionError

        """
        if not self.connection_id:
            raise eme.EngConnectionError(conn_id=self.connection_id)
        if prompt:
            self.initial_prompt = prompt
        if not self.initial_prompt:
            raise eme.EngConnectionError("Prompt is undefined")
        while True:
            # loop until one of the callbacks returns True
            # print("Event list is ", self.event_list)
            hnd_id = self.connection_id.expect(self.event_list, timeout=t_out)
            if self.callback_list[hnd_id]():
                break
        return self.results

    def _handle_timeout(self):
        """
        Handles the timeout event by raising a Runtime error

        :raises eme.EngTimeoutError: This method is run due to a Command Timeout event.

        """
        logger.error("Timeout Expired on host: {0} while running: {1}".format(self.host_name, self.last_cmd))
        if self.state != "Connected":
            # If the session is not fully connected and we recived a timeout  send a line
            # Some Term server connections require a sendline to expose the prompt
            if "ts_port" in self.options.keys():
                logger.debug("Sending empty line.")
                self.connection_id.sendline("")
            # Increment the number of timeout events while attempting to log into the device
            self.num_sendline_attempts_to_login += 1
            if self.num_sendline_attempts_to_login > 3:
                logger.debug("Timeout, dumping connection obj: <{0}>".format(self.connection_id))
                raise eme.EngConnectionError("Failed to connect to {0}, "
                                             "attempts: {1}".format(self.host_name,
                                                                    self.num_sendline_attempts_to_login))
            return False
        logger.error("Timeout Expired, Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        self.logout()
        # Do not reconnect here, inform uper layer instaed
        # if self.state == "Connected":
        #    self.reconnect()
        raise TimeoutError("Timeout Expired, prompt not found. Expected: {0}".format(self.event_list))

    def _handle_eof(self):
        """
        Handles the eof event by raising a Runtime error.  This method is called when
        the connection receives an EOF.  This will raise the error.

        :raises EOFError: This method will always raise this event since this method
                          is only called when this error is encountered

        """

        logger.error("Eof, Buffer=<{0}>".format(self.connection_id.before))
        self.logout()
        raise EOFError()

    def _handle_new_key(self, answer="yes"):
        """
        Handles the ssh request for new key event by answering answer (yes, by default)

        :param str answer: answer to adding new key question.

        :return: False,  this will have the Expect method stay in the loop
        :rtype: bool

        """
        logger.debug("New key(before): Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        self.connection_id.sendline(answer)
        logger.debug("New key(after): Buffer=<{0}>".format(self.connection_id.after.decode(errors='ignore')))
        return False

    def _handle_password(self):
        """
        Handles the request for password event by providing the password

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool

        """
        logger.debug("Password requested: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        self.connection_id.sendline(self.password)
        return False

    def _handle_cimc_confirm(self, answer="y"):
        """
        Handles power cycle confirmation event
        :param str answer: answer to confirm power cycle of UCS
        :return:
        """
        logger.debug("Confirming Power Cycle for UCS server")
        self.connection_id.sendline(answer)
        return False

    def _handle_login(self):
        """
        Handles the request for login event by providing the login

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool

        """
        logger.debug("Login detected: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        # Escape Linux display login information
        if self.connection_id.match.group(1):
            logger.debug("Login detected, but it's not a request for username")
        else:
            self.connection_id.sendline(self.user_name)
        return False

    def _handle_prompt(self):
        """
        Handles the prompt found event, fills up the results string with what was returned

        :return: True: this will have the Expect method exit the loop
        :rtype: str

        """
        logger.debug("Prompt found: Before Prompt Buffer=<{0}>\n"
                     "Prompt found: After Prompt Buffer=<{1}>".format(
                                                         self.connection_id.before.decode(errors='ignore'),
                                                         self.connection_id.after.decode(errors='ignore')))
        # Returns everything up to the prompt
        self.results = self.connection_id.before
        return True

    def _handle_generic_prompt(self):
        """
        Handles the generic prompt found event, fills up the results string with
        what was returned, ideally should set the prompt what the detected one

        :return: True: this will have the Expect method exit the loop
        :rtype: bool

        """
        logger.debug("Generic prompt found: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        logger.debug("Matched prompt: {0}".format(self.connection_id.match.group()))
        # Set prompt, READ: it causes an issue with $, needs escape, comment for now
        # self.prompt = self.connection_id.match.group()
        # Returns everything up to the prompt
        self.results = self.connection_id.before
        return True

    def _handle_cfe_break(self):
        """
        Handles the cfe break event, ut sends ctrl-c when Abort is detected

        :return:  False: this will have the Expect method stay in the loop
        :rtype: bool
        """
        logger.debug("Abort requested: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        # Send control-c
        self.connection_id.sendcontrol("c")
        return False

    def _handle_cfe_ram(self):
        """Handles the cfe ram event, ut sends ctrl-c when Abort is detected

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool
        """
        logger.debug("Abort requested: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        # Send control-c
        self.connection_id.sendcontrol("c")
        return False

    def _handle_login_shell(self):
        """
        Handles the Login Shell found event, "hits enter" when found

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool
        """
        logger.debug("Enter Login shell requested: "
                     "Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        # Press Enter
        self.connection_id.sendline("")
        return False

    def _handle_ts_option(self):
        """
        Handles the terminal server choice event, chooses 1 - Initiate a regular session

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool
        """
        logger.debug("Choice requested: Buffer=<{0}>".format(self.connection_id.before.decode(errors='ignore')))
        # Choose 1 - Initiate a regular session
        self.connection_id.sendline("1")
        return False

    def _handle_log_sdby_mio(self):
        """
        Handles the event where the connection is to the standby MIO.
        The connection is somewhat non-operational

        :return: False: this will have the Expect method stay in the loop
        :rtype: bool

        :raises EngConnectionError   Connection is not usable
        """
        logger.debug("Connection is to the standby MIO")
        raise eme.EngConnectionError("Connection is to the standby MIO: {0}".format(self.connection_id))

    def get_registered_strings(self):
        """
        Return the current registered reg ex strings to the caller

        :rtype: string
        :return: Current reg ex strings that expect is using
        """
        return self.event_list

    def _clear_registered_strings(self):
        """
        Clear the registered reg ex strings to method mappings lists

        :return: None
        """
        self.event_list = []
        self.callback_list = []

    def _register(self, event, func):
        """
        Creates 2 lists, one with the event lists and one with the event handlers,
        notice the event and event handler have same list index

        :param str/bool event: the event to be handled
        :param func: the event handler

        :return: None
        """
        self.event_list.append(event)
        self.callback_list.append(func)

    def _update_matching_list(self):
        """
        This function register an event and its associated
        associated callback function

        :return: None
        """
        # Clear out the reg ex strings and the method mappings
        self._clear_registered_strings()

        # Add the logging mapping   if the connection is not logged on
        if self.state is not "Connected":
            # Add logging in mappings
            for key, value in self.login_dict.items():
                self._register(key, value)

        # Add the exception mappings
        for key, value in self.exc_dict.items():
            self._register(key, value)

        # Set the prompt string
        # self._register(create_esc_prompt(self.prompt), self._handle_prompt)

        # If there is any entries on the list   add them
        if len(self.prompt_list) > 0:
            for prompt_str in self.prompt_list:
                self._register(create_esc_prompt(prompt_str), self._handle_prompt)

    def conn_flush(self, timeout=5):
        """
        Reads any and all characters that are in the buffer of connection.  This
        method will continue to read from the connection till a timeout is encountered.

        :param int timeout: Timeout in seconds

        :return: None
        """

        # Loop reading from the connection till no more data
        while True:
            try:
                conn_output = self.connection_id.read_nonblocking(size=1000, timeout=timeout)
                logger.debug("SSH Flush received: {0}".format(conn_output))
            except pexpect.TIMEOUT:
                logger.debug("SSH Flush received a timeout")
                break
            except pexpect.EOF:
                logger.debug("SSH Flush received a EOF")
                raise EOFError

    def login(self, timeout=60):
        """
        Opens the ssh connection or raises a Runtime error, and logs in tothe
        target device

        :param int timeout: Timeout in seconds of logging into the device

        :return: <DESC>
        :rtype: str
        :raises eme.EngConnectionError; Failure to open a connection to the device
        """
        global mlog_idx

        if not self.state == "Idle":
            raise eme.EngConnectionError("Connection not in Idle state {0}".format(self.state))

        # Create the list of matching strings to method mappings
        self._update_matching_list()

        # start off with quiet mode to suppress most warning and diag messages
        #   same as -o LogLevel=QUIET
        arg_list = ["-q"]

        # ssh options
        for option in self.ssh_options:
            arg_list.append("-o {0}".format(option))

        if "x11" in self.options.keys():
            arg_list.append("-X")
        if "ts_port" in self.options.keys():
            arg_list.append("-l :{0}".format(self.options["ts_port"]))
        else:
            arg_list.append("-l")
            arg_list.append("{0}".format(self.user_name))
        if "ssh_port" in self.options.keys():
            arg_list.append("-p {0}".format(self.options["ssh_port"]))
        arg_list.append("{0}".format(self.host_name))
        logger.debug("Spawning ssh with the following args: {0}".format(arg_list))
        try:
            # print("Arguement list {0}".format(arg_list))
            self.connection_id = pexpect.spawn("ssh", arg_list, timeout)

            # Enable debug of the connection.  The block below will record the
            # session interaction to a file
            if self.debug:
                if "ts_port" in self.options:
                    fout = open('mlog_{0}.txt'.format(self.options["ts_port"]), 'wb')
                else:
                    fout = open('mlog_{0}.txt'.format(mlog_idx), 'wb')
                    mlog_idx = mlog_idx + 1
                self.connection_id.logfile = fout
        except Exception as err:
            raise eme.EngConnectionError("Unable to open connection: {0}".format(err))

        # There was an addition to add a sendline.  Some term servers require this  and some
        # do not.  This sendline was added as well as the conn_flush() call below to handl the
        # case of some term servers requiring an extra send line   and some do not.
        self.last_cmd = "login"
        self._expect(t_out=timeout)
#       We will add flushing   if we need to   right now we do not
#        self.conn_flush(10)  We will add flushing   if we need to   right now we do not
        self.state = "Connected"
        self.num_sendline_attempts_to_login = 0
        self._update_matching_list()

    def logout(self):
        """
        Closes the connection.  Tests wether a connection id is valid and closes the connection

        :raises eme.EngConnectionError: Raised if connection ID is not set OR connection is not open
        """
        if not self.state == "Connected":
            logger.warning("Connection not in Connected state {0}, closing...".format(self.state))
        if not self.connection_id:
            raise eme.EngConnectionError(conn_id=self.connection_id)
        self.connection_id.close()
        self.state = "Idle"
        self.event_list = []
        self.callback_list = []

    def reconnect(self, attempts=240, sleep_time=5, timeout=30):
        """
        Closes connection if still there and attempts to reconnect

        :param int attempts: number of attempts
        :param int sleep_time: time to sleep before attempts
        :param int timeout: Time out in seconds of reconnecting

        :raises eme.EngConnectionError

        """
        try:
            self.logout()
        except eme.EngMibuException as err:
            logger.warning("An error occurred when closing connection {0}, proceeding...".format(err))

        success = False
        for attempt in range(0, attempts):
            try:
                self.login(timeout=timeout)
                success = True
                break
            except (eme.EngMibuException, eme.EngConnectionError, EOFError) as err:
                logger.debug("{0}, re-trying ({1}) ...".format(err, attempt + 1))
            if attempt < attempts - 1:
                time.sleep(sleep_time)
        if not success:
            raise eme.EngConnectionError("Unable to re-connect after {0} attempts".format(attempts))

    @staticmethod
    def __strip_output(command, response):
        """
        Method will Remove/Strip the response EXCEPT the actual command output

        :param str command: The Command String that was run
        :param str response: Output from the Command

        :return: The stripped output from the command
        :rtype: str

        .. note:: This method is hidden.  The method returns a modified string output
        from the command to the caller.

        """
        # remove command from response, WARNING: it might be spread over multiple lines
        lines = response.splitlines(keepends=True)
        prev_line = ""
        count = 0
        found = False
        for line in lines:
            count += 1
            line = prev_line + line.strip("\r\n")
            # search if command is found
            if command in line:
                found = True
                break
            elif count > 4:
                break
            else:
                prev_line += line
        # rebuild response string
        if not found:
            # Issuing a warning, but we could raise an exception instead
            logger.warning("Command {0} not found in buffer".format(command))
            count = 0
        response = "".join(lines[count:])

        return response

    def run_command(self, command, prompt_str=None, timeout=120, wait_for_prompt=True):
        """
        Runs a command,  expects the prompt and returns everything up to
        the prompt.

        :param str command: list of commands (strings) to be sent over the connection
        :param str prompt_str: Expected prompt.  If arg is not passed the command will use the configured one
        :param int timeout: Timeout in seconds of the command to complete
        :param bool wait_for_prompt: Default is True, if we need to wait for the prompt

        :return: str res: Command output, excluding prompt string
        :rtype: str
        :raises eme.EngConnectionError: If connection is not up
        :raises eme.EngOutputError: command is empty

        """
        if not self.state == "Connected":
            raise eme.EngConnectionError("Connection not in Connected state, "
                                         "state is: {0}, command: {1}".format(self.state, command))
        if not command:
            raise eme.EngOutputError("Command list is empty ({0})".format(command))
        if not self.connection_id:
            raise eme.EngConnectionError(conn_id=self.connection_id)
        if not prompt_str:
            prompt_str = self.initial_prompt

        logger.debug("Sending command {0}, timeout={1}, prompt={2}".format(command, timeout, self.prompt_list))
        self.last_cmd = command
        self.connection_id.sendline(command)

        if not wait_for_prompt:
            logger.warning("Do not wait for prompt, return after timeout {0}".format(timeout))
            time.sleep(timeout)
            return

        res = self._expect(prompt=prompt_str, t_out=timeout).decode(errors='ignore')

        res = self.__strip_output(command, res)

        return res

    def add_prompt(self, prompt):
        """
        Add to the the prompt list

        :param str OR list prompt: Prompt string or List of prompt strings
        :raises eme.EngProcCmd: if propmt is neither a string nor a list
        :return: None
        """

        if isinstance(prompt, str):
            self.prompt_list.append(prompt)
        elif isinstance(prompt, list):
            self.prompt_list.extend(prompt)
        else:
            raise eme.EngProcCmd("Invalid prompt argument type {0}".format(type(prompt)))
        logger.debug("Add: Prompt is now {0}".format(self.prompt_list))

    def get_promptlist(self):
        """
        Get the current prompt list

        :rtype: list
        :return: list of prompt strings
        """
        return self.prompt_list

    def set_prompt(self, prompt):
        """
        Set the desired prompt

        :param str prompt: Prompt string
        :raises eme.EngProcCmd: if propmt is neither a string nor a list
        :return: None
        """
        self.prompt_list = []
        if isinstance(prompt, str):
            self.prompt_list.append(prompt)
        elif isinstance(prompt, list):
            self.prompt_list.extend(prompt)
        else:
            raise eme.EngProcCmd("Invalid prompt argument type {0}".format(type(prompt)))

        # Update the matching list
        self._update_matching_list()
        logger.debug("Set: Prompt is now {0}".format(self.prompt_list))

    def clear_prompt(self):
        """
        Clear the prompt list

        :return: None
        """
        # clear the prompt list
        self.prompt_list = []

    def execute_command(self, command, prompt_str=None, timeout=120, check_errors=True):
        """
        Runs a command, reconnect if necessary and optionally checks for errors
        this command wraps around run_command coming from the lower level libraries

        :param str command: Command string
        :param str prompt_str: Prompt string to be used for this command.  Overrides the one to the connection
        :param int timeout: Timeout to wait for the command to complete
        :param bool check_errors: Check for errors

        :return: str res: Command output
        :rtype: str
        :raises eme.EngConnectionError

        **Example**

        >>> import libs.comms.mitg_ssh

        """
        if not self.state == "Connected":
            raise eme.EngConnectionError("Connection not in Connected state {0}".format(self.state))
        try:
            res = self.run_command(command, prompt_str=prompt_str, timeout=timeout)
        except eme.EngMibuException as err:
            raise eme.EngConnectionError("Error when running command {0}".format(err))
        if check_errors:
            error_string = ["(ERROR|ERROR_UNRECOVERED|Error|error|404):.*", "RTNETLINK answers:(.*)",
                            "Unknown command -(.*)", "\% Invalid command at \'\^\' marker", "Failure: (.*)"]
            # only first two lines
            lines = res.splitlines()[0:4]
            for line in lines:
                for err in error_string:
                    res_obj = re.search(r'{0}'.format(err), line)
                    if res_obj:
                        raise eme.EngOutputError("Error {0}".format(res_obj.group()))
        return res

    def isalive(self):
        """
        Method to check the connection status.

        :return: True when connection is up
        :rtype: bool
        """


