#!/usr/bin/env python

import pexpect
import sys
import datetime
import time
import signal

class Connect(object):

    def __init__(self, host, username, password, **options):
        #self.host = Host(host, username, password)
        #print "%s" % self.host.host
        #self.host = None
        self.host = host
        self.username = username
        self.password = password
        self.options = options
        self.ssh_options = "UserKnownHostsFile /dev/null"
        self.new_key="Are you sure you want to continue connecting \(yes/no\)\?"
        self.passwd="[pP]assword:"
        self.login="([Ll]ast)? [lL]ogin:"
        self.generic_prompt = "([^ \r\n][^\r\n]*[#>\$] ?)$"
        self.prompt = "Prompt Unknown"
        self.line_chew = "([^\r\n]*)[\r\n]+"
        self.child = ""
        self.connection_id = ""
        self.display = False

    def __Expect(self):
        if not self.connection_id:
            print "Connection is not open %s" % self.connection_id
            return False 
        retVal = True
        while True:
            self.child = self.connection_id.expect([
                         pexpect.TIMEOUT, 
                         pexpect.EOF, 
                         self.new_key, 
                         self.login, 
                         self.passwd, 
                         self.prompt,
                         self.generic_prompt])
            if self.child == 0: # Timeout
                if self.options.has_key("verbose"):
                    print "TIMEOUT: %s" % (self.connection_id.before)
                self.connection_id.close()
                retVal = False
                break
            elif self.child == 1: 
                print "EOF: %s" % (self.connection_id.before)
                self.connection_id.close()
                retVal = False
                break
            elif self.child == 2: # New key, do you want to continue? Yes
                if self.options.has_key("verbose"):
                    print "NEW_KEY: %s" % (self.connection_id.before)
                self.connection_id.sendline("yes")
                if self.options.has_key("verbose"):
                    print "NEW_KEY: %s" % (self.connection_id.after)
            elif self.child == 3: # Login
                if self.options.has_key("verbose"):
                    print "LOGIN: %s" % (self.connection_id.before)
                if (self.connection_id.match.group(1)) == "Last":
                    if self.options.has_key("verbose"):
                        print "LOGIN: Not a request for username"
                else:
                    self.connection_id.sendline(self.username)
                if self.options.has_key("verbose"):
                    print "LOGIN: %s" % (self.connection_id.after)
            elif self.child == 4: # Password
                if self.options.has_key("verbose"):
                    print "PASSWORD: %s" % (self.connection_id.before)
                self.connection_id.sendline(self.password)
                if self.options.has_key("verbose"):
                    print "PASSWORD: %s" % (self.connection_id.after)
            elif self.child == 5: # In
                if self.options.has_key("verbose"):
                    print "PROMPT: %s" % (self.connection_id.before)
                if self.display:
                    print "%s" % (self.connection_id.match.group())
                retVal = True
                break
            elif self.child == 6: # In
                if self.display:
                    print "%s" % (self.connection_id.before)
                if self.options.has_key("verbose"):
                    print "GENERIC PROMPT: %s" % (self.connection_id.match.group())
                # causes an issue with $, comment for now
                #self.prompt = self.connection_id.match.group()
                if self.options.has_key("verbose"):
                    print "GENERIC PROMPT: %s" % (self.connection_id.after)
                retVal = True
                break
            else:
                if self.options.has_key("verbose"):
                    print "UNEXPECTED: %s" % (self.connection_id.before)
                self.connection_id.close()
                retVal = True
                break
        return retVal

    def __OpenSsh(self):
        options = ""
        if self.options.has_key("port"):
            options += "-p %s" % self.options["port"]
        self.connection_id = pexpect.spawn('ssh -X -o "%s" -l %s %s %s' % (
                             self.ssh_options, self.username, options, self.host))
        return self.connection_id
        
    def __OpenTelnet(self):
        port = ""
        if self.options.has_key("port"):
            port = self.options["port"]
        self.connection_id = pexpect.spawn('telnet %s %s' % (
                             self.host, port))
        return self.connection_id

    def __SignalHandler(self, signum, frame):
        print "Interrupt handler called: %s" % (signum)
        if not self.connection_id:
            print "Connection is not open %s" % self.connection_id
            sys.exit(1)
        self.connection_id.close()
        sys.exit(0)

    def Open(self):
        signal.signal(signal.SIGINT, self.__SignalHandler)
        if self.__OpenSsh() and self.__Expect():
            return True
        if self.__OpenTelnet() and self.__Expect():
            return True
        print "Could not open connection"
        sys.exit(1)
    
    def OpenNoPrompt(self):
        signal.signal(signal.SIGINT, self.__SignalHandler)
        #if self.__OpenSsh():
        #    return True
        if self.__OpenTelnet():
            return True
        print "Could not open connection"
        sys.exit(1)

    def Run(self, cmd):
        if not self.connection_id:
            print "Connection is not open %s" % self.connection_id
            sys.exit(1)
        self.display = True
        for line in cmd.split("\n"):
            self.connection_id.sendline(line)
            self.__Expect()

    def Close(self):
        if not self.connection_id:
            print "Connection is not open %s" % self.connection_id
            sys.exit(1)
        self.connection_id.close()

    def Chew(self, cmd):
        self.connection_id.sendline(cmd)
        if not self.connection_id:
            print "Connection is not open %s" % self.connection_id
            sys.exit(1)
        while True:
            self.child = self.connection_id.expect([
                         pexpect.TIMEOUT, 
                         pexpect.EOF, 
                         self.line_chew])
            if self.child == 0: # Timeout
                if self.options.has_key("verbose"):
                    print "TIMEOUT: %s" % (self.connection_id.before)
            elif self.child == 1: 
                if self.options.has_key("verbose"):
                    print "EOF: %s" % (self.connection_id.before)
                self.connection_id.close()
                sys.exit(1)
            elif self.child == 2: # In
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                print "%s %s" % (st, self.connection_id.match.group(1))
            else:
                if self.options.has_key("verbose"):
                    print "UNEXPECTED: %s" % (self.connection_id.before)
                self.connection_id.close()
                sys.exit(1)

