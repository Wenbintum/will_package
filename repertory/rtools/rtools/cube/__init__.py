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
Tools to read and manipulate cube files.

---
Simon P. Rittmeyer, 2014-2015
simon.rittmeyer(at)tum.de
"""

from __future__ import absolute_import

from .cubebasics import *
from .interpolatedcube import *
from .cubeoperations import *

# wrapper routine...
def read_cube_val(cubefile, pos):
    """
    Wrapper routine to read and interpolate a cubefile.

    Parameters
    ----------
    cubefile : string
        Location of the cube file
    pos :  (3 x 1) array or an array thereof 
        Specifiying the position at which to evaluate the density. Note that
        vectorized calls to map_coordinates are highly efficient!

    Returns
    -------
    rho : float or (Nx1) array of floats 
        Volumetric data at the given positions. Output format depends on
        class variable convert_to_rs as given upon initialization.

    ---
    Simon P. Rittmeyer, 2014
    simon.rittmeyer(at)tum.de
    """
    # read the cube file:
    cube = InterpolatedCube(cubefile, convert = False)
    return cube(pos)
