#!/usr/bin/python
from sys import argv

# This QE-parser permits to read the outfile of a gamma-point calculation in
# QuantumEspresso and plots the local AO which contributes most to all listed
# KS-states in a projection on a local basis as performed by projwfc.x module.
# This is simply a small postprocessing script which allows to quickly identify
# a KS state. Beware that this does not take into account that some states are
# formed by equal amounts of AO basis functions (such as the p-states in
# graphene). Only trust this to identify the state belonging to a single
# impurity atom (i.e. one Lanthanoid atom above a graphene sheet, not prone to
# large hybridisation).
#
# Usage: python qe-AO-project.py pw.proj.out -2.0345
#                                 <outfile>  <fermi-level>
#
# If the Fermi level is omitted, all states are plotted.

try:
    fermi_level = float(argv[2])
    print('Fermi level given as: ' + str(fermi_level))
except:
    fermi_level = 10000
    pass

with open(argv[1], 'r') as f:
    qe_output = f.readlines()

dictstates = []

# First, parse the header information about all states
for line in qe_output:
    if '     state #' in line:
        tempdict = {'atom': 0, 'element': '', 'lm': []}
        tempdict['atom'] = int(line.split()[4])
        curline = str(line.split()[5])
        if curline.endswith(','):
            tempdict['element'] = curline[1:-3]
            tempdict['lm'] = (int(line.split()[8][-1]),
                              int(line.split()[10][-2]))
        else:
            tempdict['element'] = curline[1:-1]
            tempdict['lm'] = (int(line.split()[9][-1]),
                              int(line.split()[11][0]))
        dictstates.append(tempdict)

# Now, parse the decomposition of bloch waves

evalue = []
normalization = []
coeffs = []
states = []
wfc = []
global_read_wf = False

for line in qe_output:
    if global_read_wf:
        for subterms in line.split('+')[1:-1]:
            coeffs.append(float(subterms.split('*')[0]))
            states.append(int(subterms.split('*')[1][2:-1]))
    if '     e =' in line:
        evalue.append(float(line.split()[2]))
        global_read_wf = False
    if '     psi =' in line:
        wfc.append([coeffs, states])
        coeffs = []
        states = []
        cut_head = line.split('=')[1]
        for subterms in cut_head.split('+')[0:-1]:
            coeffs.append(float(subterms.split('*')[0]))
            states.append(int(subterms.split('*')[1][2:-1]))
        global_read_wf = True
    if '|psi|^2 =' in line:
        normalization.append(float(line.split()[2]))
        global_read_wf = False

wfc.append([coeffs, states])
wfc = wfc[1:]

# No-one is ever going to understand this slicing operation
# In essence we get the index of the highest coefficient in wfc[x][0] and then
# simply use it to obtain the corresponding AO in wfc[x][1] and print the
# information about this AO from the header read before
for bloch_state in range(len(wfc)):
    if evalue[bloch_state] < fermi_level:
        print('state: ' + str(bloch_state + 1) + ' ' + \
            str(dictstates[wfc[bloch_state][1][
                wfc[bloch_state][0].index(max(wfc[bloch_state][0]))] - 1]) + \
            ' ' + str(evalue[bloch_state]) + ' ' + \
            str(normalization[bloch_state]))
