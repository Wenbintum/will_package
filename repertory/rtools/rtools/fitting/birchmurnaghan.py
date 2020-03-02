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

#!/usr/bin/env python
"""
Some tools to fit Birch-Murnaghan's equation of state to a given dataset.

        E(V) = E0 + B0*V/B' * [(V0/V)^B' / (B'-1) + 1] - B0 V0 / (B'-1)

See also: http://en.wikipedia.org/wiki/Birch-Murnaghan_equation_of_state

Inspired by ''murn.py'' as distributed with FHIaims but geared towards modular
use.

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

import time
import numpy as np
from scipy.optimize import fmin_powell

# convenience variable to convert the bulk modulus
eV_per_Angstrom3_to_Mbar = 1.6021766208

def birch_murnaghan(V, E0, V0, B0, Bprime):
    """
    Birch Murnaghan equation

        E(V) = E0 + B0*V/B' * [(V0/V)^B' / (B'-1) + 1] - B0 V0 / (B'-1)

    See also: http://en.wikipedia.org/wiki/Birch-Murnaghan_equation_of_state

    Parameters
    ----------
    V : float
        (Atomic) volume.

    E0 : float
        Cohesive energy per atom in equilibrium.

    V0 : float
        Atomic volume in equilibrium.

    B0 : float
        Bulk modulus in equilibrium
            B := - V (dP/dV)_T
            P := - (dE/dV)_S

    Bprime : float
        Pressure derivative of B  (assumed constant in this model)
            B' := (dB/dP)_T

    Returns
    -------
    E : float
        Cohesive energy per atom.
    """


    E = E0 +  B0*V/Bprime * ((V0/V)**Bprime/(Bprime-1.)  + 1.) - (B0*V0)/(Bprime-1.)

    return E


def _initial_guess(volumina, energies):
    """
    Guess a good starting point to facilitate the fit.

    Shamelessly adapted from murn.py as distributed with FHI aims.
    """
    n = len(energies)

    E0 = np.min(energies)
    i0 = np.argmin(energies)   # index of minimum
    V0 = volumina[i0]
    if i0 > 0:
        dE_left = (energies[i0] - energies[i0-1]) / (volumina[i0] - volumina[i0-1])
        V_left = (volumina[i0] + volumina[i0-1]) / 2.
    else:
        dE_left = 0.
        V_left = volumina[i0]
    if i0 < n-1:
        dE_right = (energies[i0+1] - energies[i0]) / (volumina[i0+1] - volumina[i0])
        V_right = (volumina[i0+1] + volumina[i0]) / 2.
    else:
        dE_right = 0.
        V_right = volumina[i0]
    ddE = (dE_left - dE_right) / (V_left - V_right)
    B0 = ddE * V0
    Bprime = 3.5  # Typical value according to [1]

    return np.array([E0, V0, B0, Bprime])


def fit_birch_murnaghan(volumina, energies, logfile = 'fit_birch_murnaghan.log', **kwargs):
    """
    Fit given data to the Birch-Murnaghan equation of state.

    If no initial guess is given, it will be deduced based on simple
    analytical expressions.

    This routine uses scipy.optimize.fmin_powell to fit the data.

    Parameters
    ----------
    volumina : N-length sequence
        Atomic volumina, will enter as x-values into the fit

    energies : N-length sequence
        Corresponding cohesive energies. Will enter as y-values to the fit.

    logfile : str, optional (default = 'fit_birch_murnaghan.log')
        Path to logfile. Set to empty string if no file shall be written.

    kwargs :
        Directly passed to fmin_powell.

    Returns
    -------
    p_fitted : (4x1) array
        Optimal parameters accoring to the fit where
            popt = [E0, V0, B0, Bprime]

    func : function
        Readily parametrized Birch-Murnaghan function E(V).

    Raises
    ------
    RuntimeError if fit does not converge.
    """

    # Sort input data by volumina
    volumina, energies = np.array(sorted([zip(volumina, energies)])).transpose()

    if 'x0' not in kwargs:
        kwargs['x0'] = _initial_guess(volumina, energies)

    #internal sum of squares helper
    def sum_of_squares(param, volumina, energies):
        E_BMs = birch_murnaghan(volumina, *param)
        return np.sum((energies - E_BMs)**2)


    # Construct initial guesses

    # Optimize parameters
    p_fitted = fmin_powell(func = sum_of_squares,
                            args =(volumina, energies),
                            disp = False,
                            **kwargs)

    lim = '-'*80

    msg ="""
Birch-Murnaghan fit succeeded

(fitted on {0})

E(V) = E0 + B0*V/B' * [(V0/V)^B' / (B'-1) + 1] - B0 V0 / (B'-1)"

=== optimized parameters:

    E0 = {1:.6f}
    V0 = {2:.6f}
    B0 = {3:.6f}
    B' = {4:.6f}

    (units were not converted)
""".format(time.strftime('%c'), *p_fitted)

    print(lim)
    print(msg)
    print(lim)

    if logfile:
        with open(logfile, 'w') as f:
            f.write(msg)
            f.write('\n\n# Input data for fit')
            f.write('\n# {:>20s}{:>20s}'.format('volume (V)', 'energy (E)'))
            for V, E in zip(volumina, energies):
                f.write('\n  {:>20.9f}{:>20.12f}'.format(float(V), float(E)))


    return p_fitted, lambda V: birch_murnaghan(V, *p_fitted)

