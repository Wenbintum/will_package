#!/usr/bin/python
# coding: utf-8

import numpy as np
import sys

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

filename = sys.argv[1]
raw = []
with open(filename, "r") as f:
    raw = f.readlines()
    
cols = raw[0]
data = []
for line in raw[1:]:
    data.append([x.strip() for x in line.split()])
    
data_np = np.array(data)

peak = []
for num, line in enumerate(data):
    peak.append([num, int(line[5])])
    
peak_np = np.array(peak)


max_size = peak_np[:,1].max()
max_line = None
for num, line in enumerate(data):
    if max_size == int(line[5]):
        max_line = num
        break

print("Maximum memory allocation was: {0} (raw: {1} bytes)".format(sizeof_fmt(max_size), max_size))
print("Max size was hit in line {1}: \n {0}".format(data[max_line], max_line+2))
