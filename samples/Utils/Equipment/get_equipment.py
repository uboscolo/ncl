#!/usr/bin/env python

import sys
import subprocess
import netaddr
import re



class Equipment(object):

    def __init__(self, ip):
        self.name = None
        self.ip = ip
        self.pingable = False
        self.good_link = False

    def __Execute(self, command):
        self.res = subprocess.Popen(command, shell=True, 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.out = self.res.stdout.readlines()

    def Display(self):
        print "Equipment %s has address %s" % (self.name, self.ip)

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


class LabManager(object):

    def __init__(self, ip):
        self.name = None
        self.equipment = [ ]
        self.networks = [ ]
        self.res = None
        self.out = None
        self.dns = "labdns.mitg-tew01.cisco.com"

    def AddEquipment(self, ip):
        self.equipment.append(Equipment(ip))

    def AddNetwork(self, net):
        net_obj = netaddr.IPNetwork(net)
        self.networks.append(net_obj)

    def SweepNetworks(self):
        for net in self.networks:
            print "Checking network %s, broadcast %s, size %s ..." % (net.network, net.broadcast, net.size)
            i = 0
            for ip in net.iter_hosts():
                i += 1
                mark25 = net.size / 4
                mark50 = net.size / 2
                mark75 = net.size / 4 * 3
                if i == mark25:
                    print "25% ..."
                elif i == mark50:
                    print "50% ..."
                elif i == mark75:
                    print "75% ..."
                new_equip = Equipment(ip)
                self.equipment.append(new_equip)
                new_equip.Ping()
                new_equip.Host(self.dns)

    def Display(self):
        total_named = 0
        total_not_pingable = 0
        total_not_named = 0
        print ""
        for e in self.equipment:
            if e.name and not e.pingable:
                print "Equipment %s is not pingable" % e.name
                total_not_pingable += 1
            elif e.name:
                e.Display()
                total_named += 1
            elif e.pingable:
                print "Equipment with %s pingable but no name" % e.ip
                total_not_named += 1
        print ""
        print "Found %s named machines, %s not pingable, %s not named" % (total_named, total_not_pingable, total_not_named)

mgr = LabManager("Tewksbury")
mgr.AddNetwork("10.87.245.64/26")
mgr.AddNetwork("10.87.245.128/26")
mgr.AddNetwork("10.87.236.160/26")
mgr.AddNetwork("10.87.236.192/26")
mgr.AddNetwork("10.87.237.0/26")
mgr.AddNetwork("10.87.237.64/26")
mgr.AddNetwork("10.87.237.128/26")
mgr.AddNetwork("10.87.237.192/26")
mgr.AddNetwork("10.87.238.64/26")
mgr.AddNetwork("10.87.238.128/26")
mgr.AddNetwork("10.87.238.192/26")
mgr.AddNetwork("10.87.239.0/26")
mgr.AddNetwork("10.87.239.128/26")
mgr.AddNetwork("10.87.239.192/26")
mgr.AddNetwork("10.87.240.0/26")
mgr.AddNetwork("10.87.251.0/25")
mgr.AddNetwork("10.87.252.64/26")
mgr.AddNetwork("10.87.255.0/26")
mgr.AddNetwork("10.87.224.64/26")
mgr.SweepNetworks()
mgr.Display()

