#!/usr/bin/env python

import sys
import subprocess
import netaddr
import re



class Equipment(object):

    def __init__(self, ip, location):
        self.name = None
        self.ip = ip
        self.location = location
        self.pingable = False
        self.good_link = False

    def __Execute(self, command):
        self.res = subprocess.Popen(command, shell=True, 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        self.out = self.res.stdout.readlines()

    def __Kill(self):
        self.res.kill()

    def __Terminate(self):
        self.res.terminate()

    def __Wait(self):
        self.res.wait()
        self.res.stdout.close()

    def Display(self):
        print "Equipment %s in location %s has address %s" % (self.name, self.location, self.ip)

    def Host(self, dns):
        command = "host " + str(self.ip) + " " + dns
        self.__Execute(command)
        for line in self.out:
            res_obj = re.search(r'[\d.]+in-addr.arpa domain name pointer ([\w\d.-]+)\.', line)
            try:
                name = res_obj.group(1)
                self.name = name
            except AttributeError:
                pass
        self.__Wait()

    def Ping(self):
        command = "ping -c 2 -w 1 " + str(self.ip)
        self.__Execute(command)
        for line in self.out:
            res_obj = re.search(r'[\d]+ packets transmitted, [\d]+ received,( [\d+]+ errors ,)? ([\d]+)\% packet loss, time [\d\w]+', line)
            try:
                loss = int(res_obj.group(2))
                if loss < 100:
                    self.pingable = True
                    if not loss:
                        self.good_link = True
            except AttributeError:
                pass
        self.__Kill()

class Network(object):

    def __init__(self, network, location, contact):
        self.net = netaddr.IPNetwork(network)
        self.location = location
        self.contact = contact

    def Display(self):
        print "Network: %s, Broadcast: %s, Size: %s" % (self.net.network, self.net.broadcast, self.net.size)
        print "Location: %s, Contact: %s" % (self.location, self.contact)

    def Sweep(self, equipment, dns):
        i = 0
        inuse = 0
        for ip in self.net.iter_hosts():
            i += 1
            mark25 = self.net.size / 4
            mark50 = self.net.size / 2
            mark75 = self.net.size / 4 * 3
            if i == mark25:
                print "25% ..."
            elif i == mark50:
                print "50% ..."
            elif i == mark75:
                print "75% ..."
            new_equip = Equipment(ip, self.location)
            equipment.append(new_equip)
            new_equip.Ping()
            new_equip.Host(dns)
            if new_equip.name:
                inuse += 1
        usage = float(inuse)/(self.net.size)*100
        print "Address Space Usage %2.2f%%" % usage

class LabManager(object):

    def __init__(self, ip):
        self.name = None
        self.equipment = [ ]
        self.networks = [ ]
        self.res = None
        self.out = None
        self.dns = "labdns.mitg-tew01.cisco.com"

    def AddNetwork(self, network, location, contact):
        net = Network(network, location, contact)
        self.networks.append(net)

    def SweepNetworks(self):
        for net in self.networks:
            net.Display()
            net.Sweep(self.equipment, self.dns)

    def Display(self):
        total_named = 0
        total_not_pingable = 0
        total_not_named = 0
        print ""
        for e in self.equipment:
            if e.name and not e.pingable:
                print "Equipment %s (%s) in %s is not pingable" % (e.name, e.ip, e.location)
                total_not_pingable += 1
            elif e.name:
                e.Display()
                total_named += 1
            elif e.pingable:
                print "Equipment with ip %s in location %s is pingable but has no name" % (e.ip, e.location)
                total_not_named += 1
        print ""
        print "Found %s pingable/named machines, %s named/non-pingable, %s pingable/non-named" % (total_named, total_not_pingable, total_not_named)

mgr = LabManager("Tewksbury")
mgr.AddNetwork("10.87.236.160/27", "TEW01-335-14GH", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.236.192/26", "TEW01-335-4ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.237.0/26", "TEW01-335-5ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.237.64/26", "TEW01-335-6ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.237.128/26", "TEW01-335-7ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.237.192/26", "TEW01-335-8ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.251.0/25", "TEW01-335-9ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.238.64/26", "TEW01-335-10ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.238.128/26", "TEW01-335-11ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.238.192/26", "TEW01-335-12ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.239.0/25", "TEW01-335-13ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.239.128/26", "TEW01-335-14ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.239.192/26", "TEW01-335-15ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.240.0/26", "TEW01-335-16ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.224.64/26", "TEW01-335-18ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.245.128/26", "TEW01-335-19ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.252.64/26", "TEW01-335-20ST", "uboscolo@cisco.com")
mgr.AddNetwork("10.87.255.0/26", "TEW01-335-21ST", "uboscolo@cisco.com")
mgr.SweepNetworks()
mgr.Display()

