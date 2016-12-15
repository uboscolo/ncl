class BckgrndProcess(multiprocessing.Process):
    """ Background process.  This object provides the means to run a series of commands in
    a seperate sub process.  This process will collect the output of the commands and
    provide a way to pass the output to the main process.
    """

    def __init__(self, testbed, one_shot, *argv):
        """ INIT method of the Background process.

        :param str testbed: Testbed name
        :param bool one_shot:  True - Command list is executed 1 time.  False - Loops forever over command list
        :param tuple argv: Tuple containing commands and time out periods which are specified in seconds

        :return: None
        """

        # Call the multi-processing init method
        multiprocessing.Process.__init__(self)

        # Get the one shot flag
        self.one_shot = one_shot

        # Capture the list of args
        self.arg_vals = argv
        self.exit = multiprocessing.Event()

        # Create the Message Queue
        self.msg_queue = multiprocessing.Queue()

        # Create the event
        self.sig_event = multiprocessing.Event()

        # From the testbed name  create the platform obj
        yaml_file_loc = mitg_yaml.find_yaml_file(args.testbed)
        topo_mgr = topology_manager.TopologyManager(yaml_file_loc)
        asr5500_dev_dict = topo_mgr.get_devices_by_type(device_type="ASR5500", device_mode=ChassisMode.BOXER)
        self.asr5500_obj = asr5500_dev_dict[list(asr5500_dev_dict.keys())[0]]

        # Get the connnection from the asr devicve
        self.connection = self.asr5500_obj.boxer_cli.connection

        # Turn on timestamps
        self.connection.run_command("timestamp")

    def get_sig_event(self):
        """ Method to return the multiprocessing event object

        :rtype: Multiprocessing event object
        :return: Multiprocessing event
        """
        return self.sig_event

    def get_msg_queue(self):
        """ Method to return the multiprocessing message queue object

        :rtype: Multiprocessing message queue
        :return: Multiprocessing queue
        """
        return self.msg_queue

    def get_cmd_outputs(self):
        """ Method to return the contents of the message queue as a multi-line string

        :rtype: String
        :return: Multi-line String contained the output from the commands
        """

        # Init the command output string
        cmd_out = list()

        # Loop through getting all queue elemenets and adding to the queue
        while not msg_queue.empty():
            try:
                cmd_out = ''.join(msg_queue.get(block=False, timeout=2))
            except queue.Empty:
                break

        return(cmd_out)


    def run(self):
        """ Method called when the multiprocessing is started. Method will run a series of commands and
        sleep timeouts.  The output of the commands will be captured and sent back over the multi-processing
        message queue.

        :return: None
        """

        # Init the while flag
        while_flg = True

        # Loop over the set of commands and timeouts
        while while_flg:

            # Loop through the arguments
            for arg in self.arg_vals:
                if type(arg) == str:

                    print("Adding to queue")
                    # Call the method
                    self.msg_queue.put(self.connection.run_command(arg))
                
                else:
                    time.sleep(arg)

                # Check if the main process set the event flag   which will end the run
                if self.sig_event.is_set():
                    while_flg = False

            # If the caller specified the one shot boolean  only run the series one time
            if self.one_shot:
                break

if __name__ == '__main__':
    """ If module is run on the command line  then the following code will be run. the current implementation does not
    yet fully support dpc2 reload times - that dpc2 code requires further test/debug. the connection list is not yet
    handled properly, so, we sset the list based on the test to be run. An example of running this script
    is: python multi_proc_boot.py -i ../etc/ch25.yaml -c '((2,1),(2,2))'
    """

    # Add the parser section  Used for testing
    parser = argparse.ArgumentParser(description="parser")

    # Add testbed arg
    parser.add_argument('-i', '--testbed', dest='testbed', help='Chassis testbed file in yaml format', action='store',
                        required=True)

    # do the parsing
    args = parser.parse_args()

    # assign the values
    testbed = args.testbed

    # Create and start the background process
    bgnd_proc = BckgrndProcess(args.testbed, False, "show version", "show card table", 5, "show card table")
    bgnd_proc.start()

    # Get the signal and msg queue
    sig_event = bgnd_proc.get_sig_event()
    msg_queue = bgnd_proc.get_msg_queue()

    loop_cnt = 0
    while True:
        loop_cnt += 1
        time.sleep(1)

        if not bgnd_proc.is_alive():
            print("Bgnd proc is not running")
            break
        if loop_cnt == 60:
            print("Going to set the sig event and join")
            sig_event.set()
            bgnd_proc.join()
            break

    print("size of queue {0}".format(msg_queue.qsize()))
    command_outputs = bgnd_proc.get_cmd_outputs()

    print(command_outputs)

