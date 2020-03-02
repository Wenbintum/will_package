# This file is part of rtools.
#
#    rtools is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    rtools is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with rtools.  If not, see <http://www.gnu.org/licenses/>.

"""
Some ugly parser functions to have aims mulliken and hirshfeld partitioning
data available in some form one can work with (i.e. plotting in matplotlib). As
usual these are not pretty and pythonic but simply worked for my task at hand
and should be generic enough to work on all output files which do not have a
k-dependence

---
Georg S. Michelitsch, 2017
georg.michelitsch(at)tum.de
"""

from __future__ import print_function

import numpy as np
from os import system


def parse_mulliken(filename='Mulliken.out'):

    print('Parsing %s for Mulliken population ...' % filename)

    with open(filename, 'r') as f:
        mulliken_output = f.readlines()

    # Simply parse the number of atoms and states in the Mulliken.out file
    number_of_atoms = int(mulliken_output[np.flatnonzero(
        np.core.defchararray.find(
            mulliken_output, 'Atom number') != -1)[-1]].split()[-1][:-1])
    number_of_states = int(mulliken_output[-1].split()[0])

    full_analysis_vector = []

    # Remove all non-numeric values (i.e. comments etc)
    for line in mulliken_output:
        if line != ' \n':
            try:
                full_analysis_vector.append([float(i) for i in line.split()])
            except:
                #print 'Skipping the following line: \n %s' % line
                pass

    # Not every atom has l=3 and l=4 shells, fill these with zeroes, first
    # determine maximum l=x present
    max_length = max([len(i) for i in full_analysis_vector])

    for line_number in range(len(full_analysis_vector)):
        if len(full_analysis_vector[line_number]) < max_length:
            full_analysis_vector[line_number] += \
                [0.] * (max_length - len(full_analysis_vector[line_number]))

    # Reshape to a useful array and sum up the partial contributions
    reshaped_output = np.reshape(np.asarray(full_analysis_vector),
                                (number_of_atoms, number_of_states, 9))
    total_mulliken_charge = np.asarray(
        [sum(i) for i in reshaped_output[:, :, 3]])

    return total_mulliken_charge


def parse_hirshfeld(filename='aims.out'):

    # Inform about what you are doing
    print('Parsing %s for Hirshfeld population ...' % filename)

    # Parse the hirshfeld charges in main output file
    system('grep \'|   Hirshfeld charge        :\' ' + filename +
           ' |awk \'{print $5}\' > hirsh.dat')

    total_hirsh_charge = np.genfromtxt('hirsh.dat')

    system('rm hirsh.dat')

    return total_hirsh_charge
