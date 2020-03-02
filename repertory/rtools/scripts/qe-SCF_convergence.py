#!/usr/bin/env python
# coding: utf-8
from sys import argv

its = []
scfacc = []
totmag = []
absmag = []
time = []
energy = []

# >>> usage: qe-SCF_convergence.py filename


def parseoutput(filename):
    r""" Parse the logfile of a QuantumEspresso for SCF information

    Currently parsed information involves runtime, energy convergence and
    magnetic moments (total / absolute).

    >>> parseoutput('log')
    """
    output = open(filename)
    for line in output.readlines():
        if 'iteration #' in line:
            if line.split()[1] == '#':
                its.append(int(line.split()[2]))
            else:
                try:
                    its.append(int(line.split()[1][1:]))
                except:
                    pass
        if 'scf acc' in line:
            scfacc.append(float(line.split()[4]))
        if 'total magnetization' in line:
            totmag.append(float(line.split()[3]))
        if 'absolute magnetization' in line:
            absmag.append(float(line.split()[3]))
        if 'total cpu time spent up to now is' in line:
            time.append(float(line.split()[8]))
        if 'total energy              =' in line:
	    try:
	        energy.append(float(line.split()[3]))
	    except:
		energy.append(float(line.split()[4]))

    output.close()

if __name__ == "__main__":

    parseoutput(argv[1])

    print(" SCFNr [#] time [s]  e_tot [Ry]  e_conv [Ry]   TotMag | AbsMag [muB/cell]")
    for line in range(len(its)):
	print("#%4d    %8.2f    %8.2f    %2.4e    %+3.2f  |  %3.2f" % (its[line],
								  time[line],
								  energy[line],
								  scfacc[line],
								  totmag[line],
								  absmag[line]))
