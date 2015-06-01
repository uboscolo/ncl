#!/usr/bin/env python

import xml.etree.ElementTree as ET
from sys import argv
import sys

class ComboCallModel(object):

    def __init__(self, name, pdns):
        self.name = name
        self.total_num_pdn = pdns
        self.call_model_list = []
        self.call_model_by_name = {}

    def addCallModel(self, name, pct_pdns):
        num_pdns = int(pct_pdns * self.total_num_pdn)
        cm = CallModel(name, num_pdns)
        self.call_model_list.append(cm)
        self.call_model_by_name[name] = cm

    def displayParams(self):
        print "Combo Call Model %s - Number of PDNs: %d" % (
            self.name, self.total_num_pdn)


class CallModel(object):

    def __init__(self, name, num_pdns):
        self.name = name
        self.total_num_tool_instances = 0
        self.total_num_pdn = num_pdns
        self.total_num_ue = 0
        self.event_list = []
        self.event_by_name = {}

    def addEvent(self, name, rate, num_tool_inst, pdn_per_ue):
        print "Event: %s, Rate per PDN per hour: %.3f" % (name, rate)
        new_event = Event(name, rate)
        new_event.num_tool_inst = num_tool_inst
        new_event.pdn_per_ue = pdn_per_ue
        self.total_num_tool_instances += num_tool_inst
        self.event_list.append(new_event)
        self.event_by_name[name] = new_event

    def computeEventRates(self):
        for e in self.event_list:
            e.computeRates(self.total_num_pdn, self.total_num_tool_instances)
            self.total_num_ue += e.num_ue

    def displayEvents(self):
        for e in self.event_list:
            print "Event: %s, Num. tool instances: %d, PDN per UE: %d" % (
                e.name, e.num_tool_inst, e.pdn_per_ue)


class Event(object):

    def __init__(self, name, rate):
        self.name = name
        self.bh_rate_per_pdn = rate
        self.bh_rate_scale_factor = 1
        self.num_tool_inst = 0
        self.pdn_per_ue = 1
        self.num_pdn = 0
        self.num_ue = 0
        self.model_name = ""
        self.params_list = []

    def computeRates(self, num_pdn, num_inst):
        r = float(self.num_tool_inst) / num_inst
        self.num_pdn = num_pdn * r
        self.num_ue = self.num_pdn / self.pdn_per_ue
        rate = Rate(self.name)
        bh_rate = self.bh_rate_per_pdn / self.bh_rate_scale_factor
        rate.per_pdn_per_second = bh_rate / 3600
        rate.total_per_second = int(rate.per_pdn_per_second * num_pdn)
        rate.per_ue_per_second = rate.per_pdn_per_second / self.pdn_per_ue
        rate.display()
        callgen = CallGenerator(self.name)
        callgen.ue_count = int(self.num_ue / self.num_tool_inst)
        callgen.delay = int(self.num_ue / (rate.total_per_second / self.pdn_per_ue))
        target_make_rate = int(callgen.ue_count / callgen.delay) 
        if target_make_rate > 25:
            print "Target Make Rate too high: %d" % target_make_rate
            rate_factor = (target_make_rate / 25) + 1
            target_make_rate /= rate_factor
            print "Adjusted Target Make Rate: %d" % target_make_rate
        callgen.make_rate = target_make_rate
        callgen.init_delay = int(callgen.ue_count / callgen.make_rate)
        callgen.displayParams()


class Rate(object):

    def __init__(self, name):
        self.name = name
        self.per_pdn_per_second = 0
        self.per_ue_per_second = 0
        self.total_per_second = 0

    def display(self):
        print "--- Rates for %s ---" % self.name
        #print "Rate per PDN per second: %f/s" % self.per_pdn_per_second
        #print "Rate per UE per second: %f/s" % self.per_ue_per_second
        print "Total Rate per second: %d/s" % self.total_per_second


class CallGenerator(object):

    def __init__(self, name):
        self.name = name
        self.ue_count = 0
        self.delay = 0
        self.init_delay = 0
        self.make_rate = 0

    def displayParams(self):
        print "--- Call Parameters for %s ---" % self.name
        print "UE count: %d" % self.ue_count
        print "delay: %d" % self.delay
        print "initial_delay: %d" % self.init_delay
        print "make rate: %d" % self.make_rate
        #print "sed -i \"s/call_model \([A-Za-z0-9_\-\"]\+\) call_num \([0-9]\+\) call-make-rate \([0-9]\+\) call-break-rate \([0-9]\+\) initial-hoDelay \([0-9]\+\) hoDelay \([0-9]\+\)/call_model \\1 call_num %d call-make-rate %d call-break-rate %d initial-hoDelay %d hoDelay %d/g\"" % (self.ue_count, self.make_rate, self.make_rate, self.init_delay, self.delay)



# --------------------

#combo_model = ComboCallModel("VzW", 4320000)
#combo_model.addCallModel("4G", 1)
#cm_4g = combo_model.call_model_by_name["4G"]

#cm_4g.addEvent("lte_to_ehrpd_ho", 0.405, 40, 2)
#cm_4g.addEvent("ehrpd_to_lte_ho", 0.405, 40, 2)
#cm_4g.addEvent("pdn_act_deact", 0.56, 80, 2)
#cm_4g.addEvent("pdn_act", 1.68, 240, 2)

#cm_4g.computeEventRates()
#cm_4g.displayEvents()

# --------------------

#combo_model = ComboCallModel("AT&T", 8200000)
#combo_model.addCallModel("4G", 0.3)
#combo_model.addCallModel("3G", 0.7)
#cm_4g = combo_model.call_model_by_name["4G"]
#cm_3g = combo_model.call_model_by_name["3G"]

#cm_4g.addEvent("lte-3g-ho", 3.6, 14, 1)
#cm_4g.addEvent("makebreak-ho", 1.09, 14, 1)
#cm_4g.addEvent("s1-release", 25.2, 98, 1)
#cm_4g.addEvent("ho", 3.6, 14, 1)

#cm_4g.computeEventRates()
#cm_4g.displayEvents()

#cm_3g.addEvent("makebreak", 1.07, 170, 1)
#cm_3g.addEvent("static", 1.07, 170, 1)

#cm_3g.computeEventRates()
#cm_3g.displayEvents()

# --------------------

#combo_model = ComboCallModel("KDDI", 1310816)
#combo_model.addCallModel("v4", 0.65)
#combo_model.addCallModel("v4v6", 0.35)
#combo_model.displayParams()

#cm_v4 = combo_model.call_model_by_name["v4"]
#cm_v4.addEvent("pdn_act_deact", 10.0, 240, 1)
#cm_v4.event_by_name["pdn_act_deact"].bh_rate_scale_factor = 0.65
#cm_v4.computeEventRates()
#cm_v4.displayEvents()

#cm_v4v6 = combo_model.call_model_by_name["v4v6"]
#cm_v4v6.addEvent("lte_to_ehrpd_ho", 1.25, 40, 1)
#cm_v4v6.addEvent("ehrpd_to_lte_ho", 1.25, 40, 1)
#cm_v4v6.addEvent("s1_lte_ho", 1.25, 40, 1)
#cm_v4v6.addEvent("ehrpd_ho", 1.25, 40, 1)
#cm_v4v6.event_by_name["lte_to_ehrpd_ho"].bh_rate_scale_factor = 0.35
#cm_v4v6.event_by_name["ehrpd_to_lte_ho"].bh_rate_scale_factor = 0.35
#cm_v4v6.event_by_name["s1_lte_ho"].bh_rate_scale_factor = 0.35
#cm_v4v6.event_by_name["ehrpd_ho"].bh_rate_scale_factor = 0.35
#cm_v4v6.computeEventRates()
#cm_v4v6.displayEvents()

# --------------------

#tree = ET.parse('kddi1.xml')
#tree = ET.parse('vzw1.xml')

if sys.version_info.major < 2:
    print "Need python >= 2.x"
    exit(1)

if sys.version_info.minor < 7:
    print "Need python >= 2.7"
    exit(1)

if len(argv) != 2:
    print "Need at least one argument"
    exit(1)

script, fname = argv
tree = ET.parse(fname)

combo_model_x = tree.getroot()

combo_name = combo_model_x.attrib['name']
combo_pdns = int(combo_model_x.attrib['pdns'])
combo_model = ComboCallModel(combo_name, combo_pdns)
combo_model.displayParams()

for call_model_x in combo_model_x:
    call_model_name = call_model_x.attrib['name']
    call_model_pct_pdns = float(call_model_x.attrib['percentage_pdns'])
    combo_model.addCallModel(call_model_name, call_model_pct_pdns)
    current_cm = combo_model.call_model_by_name[call_model_name]
    for event_x in call_model_x:
        event_name = event_x.attrib['name']
        rate = float(event_x.find('target_rate').text)
        inst = int(event_x.find('instances').text)
        pdns_per_ue = int(event_x.find('pdns_per_ue').text)
        scale_f = float(event_x.find('rate_scale_factor').text)
        current_cm.addEvent(event_name, rate, inst, pdns_per_ue)
        current_cm.event_by_name[event_name].bh_rate_scale_factor = scale_f 
    current_cm.computeEventRates()
    current_cm.displayEvents()


