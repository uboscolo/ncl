""" Module containing the Telnet Connection object.
This object is used to connect to devices in order to run various commands.
"""
import telnetlib
import logging
import subprocess
import traceback
import re
import time
import libs.eng_mibu_exceptions as eme

logger = logging.getLogger(__name__)


class TelnetController(telnetlib.Telnet):
    """ Telnet base class

    Connect to remote host with TELNET and issue commands.

    """

    def __init__(self, host, user_name, password, prompt, **options):
        """
        Init Method for class

        :param str host: Hostname
        :param str user_name: User Name of the user being logged into the device
        :param str password: Login Password of the User
        :param str|list prompt: Prompt String of the Host
        :param dict **options: Options.  Currently the method doesnt use any

        :return: object: The Mitg Telnet Object

        *Example*

        >>> connection = TelnetController("mitg.cisco.com", "LedZepellin", "stairway", "Promp#")
        >>> connection.login(40)

        """
        self.host_name = host
        self.user_name = user_name
        self.password = password
        self.prompt = prompt
        self.options = options
        self.esc_prompt = None
        self.state = "Idle"
        self.protocol = "telnet"
        super().__init__(host=None)

    def __repr__(self):
        return "Telnet Connection to Host {0} state {1}".format(self.host_name, self.state)

    @staticmethod
    def __create_esc_prompt(prompt_str):
        """
        This function will take a string and return a string with the required
        characters escapped to be used for prompt matching on the telnet connection

        :param str prompt_str: Prompt String

        :return: Prompt string with characters escaped
        :rtype: str


        .. note:: This method is hidden

        """
        return prompt_str. \
            replace('[', '\['). \
            replace(']', '\]'). \
            replace('#', '\#'). \
            replace('(', '\('). \
            replace(')', '\)'). \
            replace('/', '\/'). \
            replace('*', '\*'). \
            replace('$', '\$')

    @staticmethod
    def __strip_output(command, prompt_list, response, strip_command=True):
        """
        Method will Remove/Strip the response EXCEPT the actual command output

        :param str command: The Command String that was run
        :param str response: Output from the Command
        :param bool strip_command: whether command should be stripped

        :return: The stripped output from the command
        :rtype: str

        .. note:: This method is hidden.  The method returns a modified string output
        from the command to the caller.

        """
        # remove command from response, WARNING: it might be spread over multiple lines
        if strip_command:
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
                count = 0
            response = "".join(lines[count:])

        # remove prompt at the end of response,
        # build string from prompt_list first
        prompt_str = '|'.join(prompt_list)
        response = re.sub(r'.*?' + prompt_str + r'.*?$', '', response, re.S)
        return response

    def login(self, timeout=30):
        """
        Function that will login into the specified host. The Object will contain the
        information needed to telnet to the specific chassis. First the function will
        Ping the destination to insure it is up and running.  This method will use the login
        username and password provided at the creation of the connection object.  The
        method will also set the prompt string.

        :param int timeout: Timeout value.  If one is not provided the method uses a default of 30 seconds

        :return: None
        :raises eme.EngProcCmd:
        :raises eme.EngTelnetCredentialsError: Login failure

        **Example  This example shows the user using a 40 second timeout to log in**

        >>> connection = TelnetController("mitg.cisco.com","LedZepelin","stairway","Prompt#")
        >>> connection.login(40)

        .. note:: Prior to running any comands the user should call this method to log into the device

        """

        if not self.state == "Idle":
            raise eme.EngTelnetError("Connection not in Idle state {0}".format(self.state))

        try:
            subprocess.check_call(['ping', '-c1', self.host_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            logger.warning("Failed to ping [{0}]".format(self.host_name))
            raise eme.EngPingError(ping_address=self.host_name)

        try:
            self.open(self.host_name, timeout=30)
        except:
            logger.warning("Failed to open connection to [{0}]".format(self.host_name))
            raise eme.EngTelnetError("Failed to open connection to [{0}]".format(self.host_name))

        self.state = "Connected"

        # Attempt to log into the chassis using username and password
        # Wait for login prompt
        self.run_command(None, 'login:')

        self.run_command(self.user_name, 'assword:')

        self.set_prompt(self.prompt)

        # Echo the password
        # Do not attempt to reconnect if we fail on logging into the box on
        # the first attempt
        response = self.run_command(self.password, timeout=timeout)

        if "Login incorrect" in response:
            self.logout()
            raise eme.EngTelnetCredentialsError(login=self.user_name, password=self.password)

        # print out the connection info.  Set the prompt string to the Boxer prompt
        logger.debug("host {0} : {1}".format(self.host_name, self.prompt))

    def logout(self):
        """
        Method logout: it closes the connection adn reset the state

        **Example**

        """
        if not self.state == "Connected":
            logger.warning("Connection not in Connected state {0}, closing...".format(self.state))
        self.close()
        self.state = "Idle"

    def reconnect(self, attempts=240, sleep_time=5, timeout=30):
        """
        Closes connection if still there and attempts to reconnect.  This method logs any
        exception that occurred in the logout() call

        :param int attempts: number of attempts
        :param int sleep_time: time to sleep before attempts
        :param int timeout: Timeout valus passed into the login() method when reconnecting
        :return: None

        **Example**

        >>> import libs.comms.mitg_telnet
        >>> connection = libs.comms.mitg_telnet.TelnetController("mitg.cisco.com","LedZepelin","stairway","Prompt#")
        >>> connection.reconnect()

        """
        logger.debug("Attempting to reconnect...")
        # prompt mode should not be in Telnet Module???
        # self.prompt_mode = "normal"
        self.set_prompt(self.prompt)

        if self.state != "Idle":
            # If the state is not idle, then we need to logout
            try:
                self.logout()
            except Exception as err:
                logger.warning("An error occurred when closing connection {0}, proceeding...".format(err))

        success = False
        for attempt in range(0, attempts):
            try:
                self.login(timeout=timeout)
                success = True
                break
            except eme.EngMibuException as err:
                logger.debug("{0}, re-trying ({1}) ...".format(err, attempt + 1))
            if attempt < attempts - 1:
                time.sleep(sleep_time)
        if not success:
            raise eme.EngTelnetError("Unable to re-connect after {0} attempts".format(attempts))

    def run_command(self, command, prompt_str=None, timeout=10,
                    wait_for_prompt=True):
        """
        This method will perform the work of running a command on the host. The
        function will send the command over and wait for the appropriate prompt
        string to be returned. The function will then process and send back the
        output strings returned by the host while running the command.

        :param str command: Command to run.
        :param str prompt_str: This is the prompt string to use for the command.
                               If one is not passed in then the method will use the current prompt string.
                               This is used to override the current prompt string
        :param int timeout: Timeout in seconds to wait for the command to complete. Default is 10
        :param bool wait_for_prompt: Default is True, if we need to wait for the prompt

        :return: Returns the output from the command returned by the Host
        :rtype: str
        :raises eme.EngTelnetError: Failure to run the command.
        :raises eme.EngTelnetError: Provided Prompt string is not valid type.
        :raises eme.EngTelnetError: If Telnet expect call returns and error.
                                    This method will catch these errors and return a run time


        **Example**

        """
        if not self.state == "Connected":
            raise eme.EngTelnetError("Connection not in Connected state, "
                                     "state is: {0}, command: {1}".format(self.state, command))
        if command:
            if not prompt_str:
                logger.debug("RC: CMD:{0} TO:{1} Prompt:{2} ".format(command, timeout, self.prompt, ))
            else:
                logger.debug("RC: CMD:{0} TO:{1} PassedP:{2}".format(command, timeout, prompt_str))
            # Write the command
            try:
                cmd = "{0}\n".format(command)
                self.write(cmd.encode())
            except:
                logger.error("Error {0}".format(traceback.format_exc()))
                raise eme.EngTelnetError("Failure running command")
        else:
            logger.debug("RC: CMD:None")

        if not wait_for_prompt:
            logger.warning("Do not wait for prompt, return after timeout {0}".format(timeout))
            time.sleep(timeout)
            return

        prompt_list = []
        prompt_list_str = ''
        # If the caller passes a string into the function use that string as the prompt
        if prompt_str:
            # Copy the provided prompt string into a list
            if isinstance(prompt_str, str):
                prompt_list.append(self.__create_esc_prompt(prompt_str))
            elif isinstance(prompt_str, list):
                prompt_list = list(prompt_str)
            else:
                logger.error(
                    "Error: Unknown Prompt String type in CLI command {0} Type {1}".format(command, type(prompt_str)))
                raise eme.EngTelnetError(
                    "Error: Unknown Prompt String type in CLI command {0} Type {1}".format(command, type(prompt_str)))
        else:
            if self.esc_prompt:
                if isinstance(self.esc_prompt, str):
                    prompt_list.append(self.esc_prompt)
                else:
                    prompt_list = self.esc_prompt
            else:
                raise eme.EngTelnetError("Escaped prompt is not defined, no prompt")

        # Attempt to wait for the Prompt
        try:
            logger.debug("prompt_list: {0}".format(prompt_list))
            plist = []
            for pmpt in prompt_list:
                plist.append(pmpt.encode())
            [idx, obj, response] = self.expect(plist, timeout)
        except TypeError:
            logger.error("Error {0}".format(traceback.format_exc()))
            raise eme.EngTelnetError("Failure running command, TypeError")
        except EOFError:
            logger.error("Failure running Cmd {0}, Rcvd EOFError".format(command))
            raise eme.EngTelnetError("Failure running command, EOFError")
        except Exception as err:
            logger.error("Error {0}".format(traceback.format_exc()))
            raise eme.EngTelnetError("Failure running command: {0}".format(err))

        # Check to make sure the Prompt was observed (No Timeout)
        if idx == -1:
            # No Prompt Match
            for prompts in prompt_list:
                prompt_list_str += prompts
            logger.warning("FAILURE to match prompt {0}: Cmd is {1}".format(prompt_list_str, command))
            # when nothing matches, return (-1, None, data) where data is the bytes received so far
            if not obj and response:
                logger.warning("Buffer not emtpy: <{0}>".format(response.decode(errors='ignore')))
            self.logout()
            raise eme.EngTimeoutError(prompt_list_str, command, timeout)
        logger.debug("RC Cmd:{0} Results:{1}".format(command, response.decode(errors='ignore')))

        if not command:
            return response.decode(errors='ignore')
        else:
            return self.__strip_output(command, prompt_list, response.decode(errors='ignore'))

    def get_promptlist(self):
        """
        This function will return the prompt list of the telnet session

        :return: prompt list
        :rtype: list

        """
        prompt_list = []
        if isinstance(self.prompt, str):
            prompt_list.append(self.prompt)
        else:
            prompt_list = self.prompt

        return prompt_list

    def set_prompt(self, prompt):
        """
        This function will set the prompt string to the telnet session

        :param str/list prompt: Update the current prompt string for the object
        :return: None

        **Example**

        .. note:: This will change the prompt for the connection.  Commands run after
        this call will use the NEW prompt

        """
        prompt_list = []
        if isinstance(prompt, str):
            prompt_list.append(prompt)
        else:
            prompt_list.extend(prompt)
        self.prompt = prompt_list
        self.esc_prompt = []
        for pmpt in self.prompt:
            self.esc_prompt.append(self.__create_esc_prompt(pmpt))
        logger.debug("Prompt is now {0}  Esc {1}".format(self.prompt, self.esc_prompt))

    def add_prompt(self, prompt):
        """
        This function will add to the existing prompt string to the telnet session

        :param str|list prompt: Extend the current prompt string for the object
        :return: None

        **Example**

        .. note:: This will change the prompt for the connection.  Commands run after
        this call will use the NEW prompt

        """
        if not self.prompt or not self.esc_prompt:
            raise eme.EngOutputError("Prompt or Esc prompt "
                                     "not set: {0}, Esc: {1}".format(self.prompt, self.esc_prompt))
        if not isinstance(self.prompt, list) or not isinstance(self.esc_prompt, list):
            raise eme.EngOutputError("Prompt or Esc prompt "
                                     "not in the right format: {0}, Esc: {1}".format(self.prompt,
                                                                                     self.esc_prompt))
        if isinstance(prompt, str):
            self.prompt.append(prompt)
            self.esc_prompt.append(self.__create_esc_prompt(prompt))
        else:
            for pmpt in prompt:
                self.prompt.append(pmpt)
                self.esc_prompt.append(self.__create_esc_prompt(pmpt))
        logger.debug("Prompt is now {0}  Esc {1}".format(self.prompt, self.esc_prompt))

    def execute_command(self, command, prompt_str=None, timeout=120, check_errors=True):
        """
        Runs a command, reconnect if necessary and optionally checks for errors
        this command wraps around run_command coming from the lower level libraries

        :param str command: Command string
        :param str prompt_str: Prompt string to be used for this command.  Overrides the one to the connection
        :param int timeout: Timeout to wait for the command to comlete
        :param bool check_errors: Check for errors

        :return: Command output
        :rtype: str
        :raises eme.EngTelnetError: If connection is not in the connected state
        :raises eme.EngTelnetError: Failure running the command
        :raises eme.EngTelnetError: Error occurred while reconnecting

        **Example**

        """
        if not self.state == "Connected":
            raise eme.EngTelnetError("Connection not in Connected state, "
                                     "state is: {0}, command: {1}".format(self.state, command))
        try:
            res = self.run_command(command, prompt_str=prompt_str, timeout=timeout)
        except eme.EngMibuException as err:
            raise eme.EngTelnetError("Error when running command {0}".format(err))
        if check_errors and res:
            error_string = ["(ERROR|ERROR_UNRECOVERED|Error|error|404):.*", "RTNETLINK answers:(.*)",
                            "Unknown command -(.*)", "\% Invalid command at \'\^\' marker", "Failure: (.*)"]
            # only first two lines
            lines = res.splitlines()[0:4]
            for line in lines:
                for err in error_string:
                    res_obj = re.search(r'{0}'.format(err), line)
                    if res_obj:
                        raise eme.EngTelnetError("Error {0}".format(res_obj.group()))
        return res

