#!/usr/bin/env python

import sys
import netaddr

class Interface(object):

    def __init__(self, name, type, **options):
        self.automatic = True
        self.name = name
        self.type = type
        self.options = options
        self.description = ""
        self.vlan = None
        self.vr = 0
        self.command_string = ""

    def __buildCmd(self, string):
        print "%s" % string
        self.command_string += string
        self.command_string += "\n"

    def create(self):
        self.__buildCmd("")
        self.__buildCmd(self.description)
        if (self.automatic):
            if self.options.has_key("vlan"):
                self.vlan = self.options["vlan"]
                self.name = self.name + "." + str(self.vlan)
            self.__buildCmd("auto " + self.name)
        self.__buildCmd("iface " + self.name + " inet " + self.type)
        if self.options.has_key("vr"):
            self.vr = self.options["vr"]
            self.__buildCmd("    vr " + str(self.vr))
        if self.options.has_key("ipv4Net") and self.options.has_key("ipv4Mask"):
            v4addr = self.options["ipv4Net"] + "/" + self.options["ipv4Mask"]
            v4net = netaddr.IPNetwork(v4addr)
            v4startIp = netaddr.IPAddress(int(v4net.ip) + 11)
            self.__buildCmd("    address " + str(v4startIp))
            self.__buildCmd("    netmask " + str(v4net.netmask))
            self.__buildCmd("    network " + str(v4net.ip))
            self.__buildCmd("    broadcast " + str(v4net.broadcast))
        if self.options.has_key("qlen"):
            self.__buildCmd("    up ip link set dev " + self.name + " qlen " +
                str(self.options["qlen"]))
        if self.options.has_key("sysctl"):
            self.__buildCmd("    up setvr " + str(self.vr) + " sysctl " +
                self.options["sysctl"])
        if self.options.has_key("ipv6Net") and self.options.has_key("ipv6Mask"):
            v6addr = self.options["ipv6Net"] + "/" + self.options["ipv6Mask"]
            v6net = netaddr.IPNetwork(v6addr)
            v6startIp = netaddr.IPAddress((int(v6net.ip) + int(11)), 6)
            self.__buildCmd("    up setvr " + str(self.vr) + " ip -6 addr add " +
                str(v6startIp) + "/" + self.options["ipv6Mask"] + " dev " + self.name)
        if self.options.has_key("num_addr"):
            v4startIp2 = netaddr.IPAddress(int(v4startIp) + 1) 
            v4endIp = netaddr.IPAddress(int(v4startIp) +
                int(self.options["num_addr"]) - 1)
            for v4idx in netaddr.iter_iprange(v4startIp2, v4endIp):
                self.__buildCmd("    up setvr " + str(self.vr) + " ip addr add " + 
                    str(v4idx) + "/32 dev " + self.name)
            v6startIp2 = netaddr.IPAddress(int(v6startIp) + 1, 6) 
            v6endIp = netaddr.IPAddress(int(v6startIp) + 
                int(self.options["num_addr"]) - 1, 6)
            for v6idx in netaddr.iter_iprange(v6startIp2, v6endIp):
                self.__buildCmd("    up setvr " + str(self.vr) + " ip -6 addr add " +
                    str(v6idx) + "/128 dev " + self.name)

    def add(self, **options):
        if options.has_key("ipv4Net") and options.has_key("ipv4Mask"):
            v4addr = options["ipv4Net"] + "/" + options["ipv4Mask"]
            v4net = netaddr.IPNetwork(v4addr)
            v4startIp = netaddr.IPAddress(int(v4net.ip) + 11)
            self.__buildCmd("    up setvr " + str(self.vr) + " ip addr add " +
                str(v4startIp) + "/" + options["ipv4Mask"] + " dev " + self.name)
        if options.has_key("ipv6Net") and options.has_key("ipv6Mask"):
            v6addr = options["ipv6Net"] + "/" + options["ipv6Mask"]
            v6net = netaddr.IPNetwork(v6addr)
            v6startIp = netaddr.IPAddress((int(v6net.ip) + int(11)), 6)
            self.__buildCmd("    up setvr " + str(self.vr) + " ip -6 addr add " +
                str(v6startIp) + "/" + options["ipv6Mask"] + " dev " + self.name)
        if options.has_key("num_addr"):
            v4startIp2 = netaddr.IPAddress(int(v4startIp) + 1) 
            v4endIp = netaddr.IPAddress(int(v4startIp) + 
                      int(options["num_addr"]) - 1)
            for v4idx in netaddr.iter_iprange(v4startIp2, v4endIp):
                self.__buildCmd( "    up setvr " + str(self.vr) + " ip addr add " +
                    str(v4idx) + "/32 dev " + self.name)
            v6startIp2 = netaddr.IPAddress(int(v6startIp) + 1, 6) 
            v6endIp = netaddr.IPAddress(int(v6startIp) + 
                      int(options["num_addr"]) - 1, 6)
            for v6idx in netaddr.iter_iprange(v6startIp2, v6endIp):
                self.__buildCmd("    up setvr " + str(self.vr) + " ip -6 addr add " + 
                    str(v6idx) + "/128 dev " + self.name)

    def addMgmtFirewall(self):
        self.__buildCmd("    up iptables -A FORWARD -o " + self.name + 
            " -j REJECT --reject-with icmp-net-prohibited")


class Interfaces(object):

    def __init__(self, **options):
        self.loopback = None
        self.management = None
        self.service = {}
        self.service_vr = {}
        self.options = options
        self.vlan_offset = 128
        self.vr_offset = 20
        self.description = "# This file describes the network interfaces available on your system\n# and how to activate them. For more information, see interfaces(5).\n"
        self.command_string = ""

    def __buildCmdString(self, target):
        # clear target
        self.command_string = "\"\" > " + target + "\n"
        # newspaces in string need to be handled
        cmd_string = self.description
        cmd_string += self.loopback.command_string
        cmd_string += self.management.command_string
        for k in sorted(self.service.keys()): 
            cmd_string += self.service[k].command_string
        for k in sorted(self.service_vr.keys()): 
            cmd_string += self.service_vr[k].command_string
        for line in cmd_string.split("\n"):
            self.command_string += "echo \"" + line + "\" >> " + target + "\n"


    def Transfer(self, hostname, user, password, target_file):
        # remove from here
        from myconnect import *
        self.__buildCmdString(target_file)
        options = {}
        #options["verbose"] = True
        c = Connect(hostname, user, password, **options)
        c.Open()
        c.Run(self.command_string)
        c.Close()

    def Display(self, hostname, user, password, target_file):
        self.__buildCmdString(target_file)
        print "%s" % hostname
        print "%s" % self.command_string

    def Create(self, index, num_vrs, eth_list):
        print "%s" % self.description
        if self.options.has_key("vlan_offset"):
            self.vlan_offset = self.options["vlan_offset"]
        self.loopback = Interface("lo", "loopback")
        self.loopback.description = "# The loopback network interface"
        self.loopback.create()
        self.management = Interface("eth0", "dhcp")
        self.management.description = "# Lab Management"
        self.management.create()
        self.management.addMgmtFirewall()
        for eth in range(len(eth_list)):
            options = {}
            options["qlen"] = 10000
            self.service[eth] = Interface(eth_list[eth], "static", **options)
            self.service[eth].description = "# Service " + eth_list[eth]
            self.service[eth].create()
        for vr in range(1, int(num_vrs) + 1):
            options = {}
            options["vr"] = vr
            vlan1000 = 1000 + int(index) + ((vr - 1) * self.vlan_offset)
            options["vlan"] = vlan1000
            index1000 = int(index) + ((vr - 1) * self.vlan_offset)
            options["ipv4Net"] = "192.168." + str(index1000) + ".0"
            options["ipv4Mask"] = "24"
            hex_index1000 = hex(index1000).split("x")[1]
            options["ipv6Net"] = "2001:db8:a8:" + str(hex_index1000) + "::0"
            options["ipv6Mask"] = "64"
            options["sysctl"] = "-p"
            options["num_addr"] = "40"
            if num_vrs % len(eth_list):
                print "Number of Vrs and eth ports mismatch"
                sys.exit(1)
            eth_index = (vr - 1) / (num_vrs / len(eth_list))
            eth = eth_list[eth_index]
            self.service_vr[vlan1000] = Interface(eth, "static", **options)
            self.service_vr[vlan1000].description = "# Service " + str(vlan1000)
            self.service_vr[vlan1000].create()
            server_vr = vr + self.vr_offset
            options = {}
            options["vr"] = server_vr
            vlan2000 = 2000 + int(index) + ((vr - 1) * self.vlan_offset)
            options["vlan"] = vlan2000
            index2000 = int(index) + ((vr - 1) * self.vlan_offset)
            options["ipv4Net"] = "192.188." + str(index1000) + ".0"
            options["ipv4Mask"] = "24"
            hex_index2000 = hex(index2000).split("x")[1]
            options["ipv6Net"] = "2001:db8:bc:" + str(hex_index2000) + "::0"
            options["ipv6Mask"] = "64"
            options["sysctl"] = "-p"
            options["num_addr"] = "40"
            eth_index = (vr - 1) / (num_vrs / len(eth_list))
            eth = eth_list[eth_index]
            self.service_vr[vlan2000] = Interface(eth, "static", **options)
            self.service_vr[vlan2000].description = "# Service " + str(vlan2000)
            self.service_vr[vlan2000].create()
            options = {}
            options["vr"] = vr
            vlan3000 = 3000 + int(index) + ((vr - 1) * self.vlan_offset)
            options["vlan"] = vlan3000
            index3000 = int(index) + ((vr - 1) * self.vlan_offset)
            options["ipv4Net"] = "192.148." + str(index3000) + ".0"
            options["ipv4Mask"] = "24"
            hex_index3000 = hex(index3000).split("x")[1]
            options["ipv6Net"] = "2001:db8:94:" + str(hex_index3000) + "::0"
            options["ipv6Mask"] = "64"
            #options["sysctl"] = "-p"
            options["num_addr"] = "40"
            eth_index = (vr - 1) / (num_vrs / len(eth_list))
            eth = eth_list[eth_index]
            self.service_vr[vlan3000] = Interface(eth, "static", **options)
            self.service_vr[vlan3000].description = "# Service " + str(vlan3000)
            self.service_vr[vlan3000].create()
            options = {}
            options["ipv4Net"] = "192.208." + str(index3000) + ".0"
            options["ipv4Mask"] = "24"
            options["ipv6Net"] = "2001:db8:d0:" + str(hex_index3000) + "::0"
            options["ipv6Mask"] = "64"
            self.service_vr[vlan3000].add(**options)

