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
Some tools for all of us that periodically have to work with castep.
Most of the tasks may be as well done with the castep calculator, but these
functions are comparably easy to tweak...

---
Simon P. Rittmeyer, 2013-2015
simon.rittmeyer(at)tum.de
"""

from __future__ import print_function

import numpy as np
from ase.io.castep import read_castep_cell
import os


def read_pattern(castepfile,
                  pattern,
                  get_status = False,
                  verbose = False,
                  ):
    """
    function to read from a castepfile according to a specified pattern

    Arguments:
    ---------

    castepfile : string
        absolute directory of the castepfile to read

    pattern : 2-tuple of strings, [str,str]
        the first pattern, pattern[0], specifies which line to read;
        the second pattern, pattern[1], specifies the operation to read something
        from this line, i.e. line.split() [note, variable 'line' has to be included in pattern[1]]

    get_status : boolean (default False)
        enabling to get status of the CASTEP-calculation within specified file
        Will be a converged and finihed boolean variable.

    verbose : boolean (default False)
        enabling verbosity
    """


    if verbose:
        print('reading {}'.format(castepfile))

    d = []

    with open(castepfile, 'r') as f:
        finished = False
        converged = False
        geo_opt = False
        for line in f:
            # check if this is a geometry optimization
            if 'type of calculation' in line:
                task = line.split(':')[1].strip()
                if task == 'geometry optimization':
                    geo_opt = True
            if pattern[0] in line:
                if type(eval(pattern[1])) is list:
                    d.append([float(i) for i in eval(pattern[1])])
                else:
                    d.append(float(eval(pattern[1])))
                converged = True
            if '*Warning* max. SCF cycles performed but system has not reached the groundstate.' in line:
                converged = False
            if '  Warning: electronic minimisation did not converge when finding ground state.' in line:
                converged = False
            if line.startswith('Total time          ='):
                finished = True
            if line.startswith('  Writing checkpoint file...'):
                finished = True
            if geo_opt == True:
                if 'Geometry optimization completed successfully' in line:
                    converged = True
                if 'Geometry optimization failed' in line:
                    converged = False
    # do not return number if not finished or converged
    if not all([converged, finished]):
        d = [np.nan]
    if not get_status:
        return d

    else:
        return d, finished, converged


def read_cellfile(cellfile, verbose=False):
    if verbose:
        print('reading position from cell-file: {}'.format(cellfile))
    pos = read_cell(cellfile).get_positions()
    return pos


def read_fcc_bulk_lattice_constant(castepfile):
    d = 'not available'
    resultsfile = open(castepfile, 'r').readlines()
    for i in xrange(len(resultsfile)):
        if resultsfile[i].startswith('        Real Lattice(A)'):
            d = float(resultsfile[i+1].split()[1])*2
    return d


def read_castepfile(source,
                    pattern_par,
                    pattern_var = None,
                    verbose = False,
                    get_status = False):
    """
    Wrapper around read_pattern functionality.
    Reads parameter and variable value from '.castep'-files contained in
    source-directory versus parameter specified by pattern, returns list of
    tuples: list([parameter, variable])

    Arguments:
    ---------

    source : string
        directory to search for '.castep'-files

    pattern_par : 2-tuple of strings
        list containing the entries of the pattern to read in a specific line of
        the '.castep'-file and the pattern to get a specific value of this line
        (e.g. see pattern in read_energy function)

    pattern_var : 2-tuple of strings (default: None, energy will be read out)
        list containing the entries of the pattern to read in a specific line of
        the '.castep'-file and the pattern to get a specific value of this line
        (e.g. see pattern in read_energy function)

    readcell : boolean (default False)

    Returns:
    ---------

    data : list of 2-tuples, list([par,var])
        list of 2-tuples, containing the parameter and variable according to
        the specified patterns

    """


    # default to read in the energy from "castep"-file
    if pattern_var == None:
        read = read_energy
    else:
        read = read_pattern(pattern = pattern_var)

    data = []

    for dirpath, dirname, files in os.walk(source):
        for f in files:
            if f.endswith('.castep'):

                # get absolute path fo file
                f = os.path.abspath(os.path.join(dirpath,f))

                # read out variable
                var = read(castepfile = f)

                # read out parameter
                par = read_pattern(castepfile = f,
                                   pattern = pattern_par,
                                   verbose = verbose,
                                   get_status = get_status)
                data.append([par ,var ])


    return data


def read_energy(castepfile,
                get_status = False,
                verbose = False,
                readpos = False,
                readcell = False):

    """
    Wrapper around read_pattern functionality.
    Reads total energy value from single '.castep'-file specified by input


    Arguments:
    ---------

    castepfile : string
        directory to search for '.castep'-files

    get_status : boolean (default False)
        enabling to get status of the CASTEP-calculation within specified file

    verbose : boolean (default False)
        enabling verbosity

    read_pos : boolean (default False)

    readcell : boolean (default False)


    Returns:
    ---------

    out : float
        energy of the input '.castep'-file
    """

    # pattern to read out the energy from a given '.castep'-file
    pattern= ["NB est. 0K energy (E-0.5TS)      =",
              "line.split('=')[1].strip().split()[0]"]

    out = read_pattern(castepfile = castepfile,
                       pattern = pattern,
                       get_status = get_status,
                       verbose = verbose,
                       )

    if not out[-1]:
        pattern= ["Final energy =",
                  "line.split('=')[1].strip().split()[0]"]
        out2 = read_pattern(castepfile = castepfile,
                       pattern = pattern,
                       get_status = get_status,
                       verbose = verbose,
                       )
        if out2[-1]:
            out = out2
    # return only last energy entrance of '*.castep' file
    if get_status:
        out = [out[0][-1], out[1], out[2]]

    else:
        out = out[-1]
    return out








