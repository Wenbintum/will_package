#!/usr/bin/env python
# coding: utf-8
from lxml import etree
import sys
import subprocess
import os
import csv

def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    Backported from Python 2.7 as it's implemented as pure python on stdlib.

    >>> check_output(['/usr/bin/python', '--version'])
    Python 2.6.2
    """
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output

nodes = check_output(['pbsnodes', '-x'])

parser = etree.XMLParser(ns_clean=True, recover=True)
root = etree.fromstring(nodes, parser)

state = []
np = []
properties = []
status = []
tick = []
tot_mem = []
tot_mem_gb = [] 
cpu = []
os_version = []

# convert kb to gb. we can haz more numbers!
kbtogb = 9.5367431640600002e-07

for num, i in enumerate(root):
    np.append((i.xpath('np'))[0].text)
    properties.append((i.xpath('properties'))[0].text)
    try:
        status.append([num+1, (i.xpath('status'))[0].text])
    except:
        status.append([num+1, "totmem=Offline"])
    tick.append("tick" + str(num+1))

for num, i in enumerate(root):
    string = ((i.xpath('state'))[0].text).strip()
    if string == "job-exclusive":
        state.append("up")
    elif string == "free":
        state.append("up")
    else:
        state.append(string.replace("job-exclusive", ""))
    
# get CPU and os_version
# "hardcoded" position for cpu and os!

for i in properties:
    cpu.append("!"+str(i.split(",")[0]))
    try:
        os_version.append(i.split(",")[6])
    except:
        os_version.append("no os_flag")

#get total memory
for i in status:
    t_stats = i[1].split(",")
    tot_mem.append((next(x for x in t_stats if "totmem" in x)).split("=")[-1].replace("kb", ""))

for i in tot_mem:
    try:
        tot_mem_gb.append(str(int(float(i)*kbtogb)) + " gb")
    except:
        tot_mem_gb.append("???")

all_list = zip(tick, np, cpu, os_version, tot_mem_gb, state)

table_header_ext = "| *Node Name* | *cores* | *CPU* | *os_version* | *RAM* | *state* |"

print(table_header_ext)
for row in all_list:
    print("| " + " | ".join(row) + " |")

print("\n")
print("Currently online: {0} / {1} compute nodes.".format(state.count("up"), len(state)))
