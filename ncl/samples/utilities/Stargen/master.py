import sys
import math

class Master(object):

    def __init__(self, name, **options):
        self.name = name
        self.options = options
 
    def createServers(self, id):
        for vr in range(1, self.options["num_vr"] + 1):
            cnt = 1
            while(cnt <= self.options["num_inst"]):
                new_id = id + ((vr -1) * self.options["addr_offset"])
                hostname = self.options["prefix"] + str(id) + "." + self.options["suffix"]
                stargen_handle = "s-" + str(new_id) + "-" + str(cnt + 10)
                stargen_protocol = self.options["protocol"] + "Server"
                stargen = Stargen(stargen_handle)
                stargen.host = hostname
                stargen.affinity = int(math.pow(2, (cnt - 1 + ((vr - 1) * self.options["core_offset"]))))
                stargen.vr = str(vr + self.options["vr_offset"])
                stargen.generator = stargen_protocol
                stargen.rsa = "192.188." + str(new_id) + "." + str(cnt + 10)
                stargen.rv6sa = "2001:db8:bc:" + format((new_id), "x") + "::" + format((cnt + 10), "x")
                stargen.dst_port = stargen.dst_port_table[cnt - 1]
                stargen.xml_file = stargen.xml_table[cnt - 1]
                stargen.display_server()
                cnt += 1

    def createClients(self, id):
        for vr in range(1, self.options["num_vr"] + 1):
            cnt = 1
            while(cnt <= self.options["num_inst"]):
                new_id = id + ((vr -1) * self.options["addr_offset"])
                hostname = self.options["prefix"] + str(id) + "." + self.options["suffix"]
                stargen_handle = "c-" + str(new_id) + "-" + str(cnt + 10)
                stargen_protocol = self.options["protocol"] + "Gen"
                stargen = Stargen(stargen_handle)
                stargen.host = hostname
                stargen.affinity = int(math.pow(2, (cnt - 1 + ((vr - 1) * self.options["core_offset"]))))
                stargen.vr = str(vr)
                stargen.generator = stargen_protocol
                stargen.rsa = "192.188." + str(new_id) + "." + str(cnt + 10)
                stargen.rv6sa = "2001:db8:bc:" + format((new_id), "x") + "::" + format((cnt + 10), "x")
                stargen.src_port = 5050 + cnt
                stargen.dst_port = stargen.dst_port_table[cnt - 1]
                stargen.xml_file = stargen.xml_table[cnt - 1]
                stargen.callgen = Callgenerator("lattice_clp")
                stargen.callgen.affinity = cnt - 1 + ((vr - 1) * self.options["core_offset"])
                stargen.callgen.clp += (cnt - 1) * -3
                stargen.callgen.tunnel_name = "tun" + str(new_id) + "-" + str((cnt - 1))
                stargen.callgen.call_model = CallModel(stargen.callgen.call_model_table[cnt - 1])
                stargen.callgen.call_model.addNetwork("PGW::GTP", "ipv4")
                stargen.callgen.call_model.networks["PGW::GTP"].local_control_ip = "192.168." + str(new_id) + "." + str(cnt + 10)
                stargen.callgen.call_model.networks["PGW::GTP"].local_data_ip = "192.168." + str(new_id) + "." + str(cnt + 10)
                stargen.callgen.call_model.networks["PGW::GTP"].remote_control_ip = "193.50.1.107"
                stargen.callgen.call_model.networks["PGW::GTP"].remote_data_ip = "193.50.1.107"
                stargen.callgen.call_model.addNetwork("PGW::PMIP", "ipv6")
                stargen.callgen.call_model.networks["PGW::PMIP"].local_control_ip = "2001:db8:a8:" + format((new_id), "x") + "::" + format((cnt + 10), "x")
                stargen.callgen.call_model.networks["PGW::PMIP"].local_data_ip = "2001:db8:a8:" + format((new_id), "x") + "::" + format((cnt + 10), "x")
                stargen.callgen.call_model.networks["PGW::PMIP"].remote_control_ip = "2001:db8:c1:35::16a"
                stargen.callgen.call_model.networks["PGW::PMIP"].remote_data_ip = "2001:db8:c1:35::16a"
                # changed for 1 APN
                stargen.callgen.call_model.addApn("internet-1", "ipv4")
                stargen.callgen.call_model.addApn("internet-dcca-1", "ipv4")
                #stargen.callgen.call_model.addApn("ims-1", "ipv6")
                #stargen.callgen.call_model.addApn("internet-dcca-1", "ipv4v6")
                apn3Name = str(new_id) + "-" + str(cnt + 10) + "-ipv4ipv6-1"
                stargen.callgen.call_model.addApn(apn3Name, "ipv4v6")
                #stargen.callgen.call_model.apns[0].qci = 5
                stargen.callgen.call_model.identifier.host_id = format(new_id, "03d")
                stargen.callgen.call_model.identifier.instance_id = cnt % 10
                stargen.display_client()
                cnt += 1



class Stargen(object):

    def __init__(self, handle):
        self.handle = handle
        self.host = None
        self.affinity = 0
        self.vr = 0
        self.generator = None
        self.rsa = None
        self.rv6sa = None
        self.dst_port = None
        self.src_port = None
        self.dst_port_table = [80, 80, 53, 80, 80, 80, 80, 443, 443, 443]
        self.xml_file = None
        #self.xml_table = [ "/localdisk/xml-files/HTTP/6_gets_1_trans_ehrpd.xml",
        #                   "/localdisk/xml-files/HTTP/6_gets_1_trans_ehrpd.xml",
        #                   "/localdisk/xml-files/DNS/dns-multi-trans.xml",
        #                   "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
        #                   "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
        #                   "/localdisk/xml-files/HTTP/6_gets_1_trans_large_get.xml",
        #                   "/localdisk/xml-files/HTTP/6_gets_1_trans_large_get.xml",
        #                   "/localdisk/xml-files/HTTP/6_gets_1_trans_large_get.xml",
        #                   "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
        #                   "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml" ]
        self.xml_table = [ "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml",
                           "/localdisk/xml-files/HTTP/1_get_1_trans_50KB.xml" ]
        self.callgen = None

 
    def display_server(self):
        master_string = "create_server {"
        master_string += self.host
        master_string += " affinity " + str(self.affinity)
        master_string += " vr " + str(self.vr)
        master_string += " handle " + self.handle
        master_string += " stargen_generator " + self.generator
        master_string += " rsa " + self.rsa
        master_string += " rv6sa " + self.rv6sa
        master_string += " dst_port " + str(self.dst_port)
        master_string += " xml_file " + self.xml_file
        master_string += "}"
        print "%s" % master_string 

    def display_client(self):
        master_string = "create_client {"
        master_string += self.host
        master_string += " vr " + str(self.vr)
        master_string += " af " + str(self.callgen.affinity)
        master_string += " affinity " + str(self.affinity)
        master_string += " handle " + self.handle
        master_string += " callgen_type " + self.callgen.type
        master_string += " clp " + str(self.callgen.clp)
        master_string += " call_model " + "\"" + self.callgen.call_model.name + "\""
        master_string += " " + self.callgen.call_model_params[self.callgen.call_model.name]
        master_string += " stargen_generator " + self.generator
        master_string += " rsa " + self.rsa
        master_string += " rv6sa " + self.rv6sa
        master_string += " src_port " + str(self.src_port)
        master_string += " dst_port " + str(self.dst_port)
        master_string += " xml_file " + self.xml_file
        master_string += " mcc " + str(self.callgen.call_model.network_id.mcc)
        master_string += " mnc " + str(self.callgen.call_model.network_id.mnc)
        master_string += " tac " + str(self.callgen.call_model.network_id.tac)
        master_string += " sgw-control-ip " + str(self.callgen.call_model.networks["PGW::GTP"].local_control_ip)
        master_string += " hsgw-control-ip " + str(self.callgen.call_model.networks["PGW::PMIP"].local_control_ip)
        master_string += " apn1Name " + self.callgen.call_model.apns[0].name
        master_string += " apn1Type " + self.callgen.call_model.apns[0].type
        master_string += " apn1Qci " + str(self.callgen.call_model.apns[0].qci)
        master_string += " apn2Name " + self.callgen.call_model.apns[1].name
        master_string += " apn2Type " + self.callgen.call_model.apns[1].type
        master_string += " apn2Qci " + str(self.callgen.call_model.apns[1].qci)
        master_string += " apn3Name " + self.callgen.call_model.apns[2].name
        master_string += " apn3Type " + self.callgen.call_model.apns[2].type
        master_string += " apn3Qci " + str(self.callgen.call_model.apns[2].qci)
        master_string += " hostId " + str(self.callgen.call_model.identifier.host_id)
        master_string += " instanceId " + str(self.callgen.call_model.identifier.instance_id)
        master_string += " custId " + self.callgen.call_model.identifier.cust_id
        master_string += " s11-ip " + str(self.callgen.call_model.networks["PGW::GTP"].local_control_ip)
        master_string += " pgw-ip " + str(self.callgen.call_model.networks["PGW::GTP"].remote_control_ip)
        master_string += " lma-ip " + str(self.callgen.call_model.networks["PGW::PMIP"].remote_control_ip)
        master_string += " sgw-data-ip " + str(self.callgen.call_model.networks["PGW::GTP"].local_data_ip)
        master_string += " hgw-data-ip " + str(self.callgen.call_model.networks["PGW::PMIP"].local_data_ip)
        master_string += " pgw-ip-data " + str(self.callgen.call_model.networks["PGW::GTP"].remote_data_ip)
        master_string += " lma-ip-data " + str(self.callgen.call_model.networks["PGW::PMIP"].remote_data_ip)
        master_string += " ltc_tun_name " + self.callgen.tunnel_name
        #master_string += " bind_hsgw bind"
        master_string += "}"
        print "%s" % master_string 


class Callgenerator(object):

    def __init__(self, type):
        self.type = type
        self.affinity = 0
        self.clp = 65000
        self.tunnel_name = None
        self.call_model = None
#        self.call_model_table = [ "2PDN-ehrpd-lte-ho",
#                                  "2PDN-lte-ehrpd-ho",
#                                  "2PDN-static",
#                                  "2PDN-static",
#                                  "2PDN-static",
#                                  "2PDN-static",
#                                  "2PDN-static",
#                                  "2PDN-static",
#                                  "2PDN-makebreak-data",
#                                  "2PDN-makebreak-data" ]
#        self.call_model_params = { 
#            "2PDN-ehrpd-lte-ho" : "call_num 12500 call-make-rate 14 call-break-rate 14 initial-hoDelay 888 hoDelay 892",
#            "2PDN-lte-ehrpd-ho" : "call_num 12500 call-make-rate 14 call-break-rate 14 initial-hoDelay 888 hoDelay 892",
#            "2PDN-static" : "call_num 12500 call-make-rate 9 call-break-rate 9 pdnDelay 5 pdnDelay2 5",
#            "2PDN-makebreak-data" : "call_num 12500 call-make-rate 9 call-break-rate 9 pdnDelay 1388 pdnDelay2 1286" }
#        self.call_model_table = [ "1PDN-makebreak-data",
#                                  "1PDN-makebreak-data",
#                                  "1PDN-static",
#                                  "1PDN-static",
#                                  "1PDN-static",
#                                  "1PDN-static",
#                                  "1PDN-static",
#                                  "1PDN-static",
#                                  "1PDN-makebreak-data",
#                                  "1PDN-makebreak-data" ]
        self.call_model_table = [ "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static",
                                  "1PDN-static" ]
        self.call_model_params = { 
            "1PDN-static" : "call_num 27300 call-make-rate 24 call-break-rate 24 pdnDelay 5 pdnDelay2 5",
            "1PDN-makebreak-data" : "call_num 27300 call-make-rate 24 call-break-rate 24 pdnDelay 1137 pdnDelay2 1137" }



class CallModel(object):

    def __init__(self, name):
        self.name = name
        self.call_num = 0
        self.call_make_rate = 0
        self.call_break_rate = 0
        self.initial_delay = 0
        self.delay = 0
        self.network_id = NetworkId("Default")
        self.identifier = Identifier(name)
        self.networks = {}
        self.apns = []

    def addNetwork(self, name, type):
        if name == "PGW::GTP":
            self.networks[name] = PgwGtpNetwork(name, type)
        elif name == "PGW::PMIP":
            self.networks[name] = PgwPmipNetwork(name, type)
        else:
            pass
            
    def addApn(self, name, type):
        self.apns.append(Apn(name, type))

class NetworkId(object):

    def __init__(self, name):
        self.name = name
        self.mcc = 480
        self.mnc = 311 
        self.tac = 212


class Identifier(object):

    def __init__(self, name):
        self.name = name
        self.host_id = 0
        self.instance_id = 0
        self.cust_id = "\"\""


class Network(object):

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.local_control_ip = None
        self.remote_control_ip = None
        self.local_data_ip = None
        self.remote_data_ip = None


class PgwGtpNetwork(Network):

    def __init__(self, name, type):
        super(PgwGtpNetwork, self).__init__(name, type)


class PgwPmipNetwork(Network):

    def __init__(self, name, type):
        super(PgwPmipNetwork, self).__init__(name, type)


class Apn(object):

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.qci = 9
          
