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

from __future__ import print_function, absolute_import

# os operations
import os

# file io
from time import strftime

# linear algebra
from numpy import swapaxes, nan
from numpy.ma import masked_less_equal

# 3D interpolation
from scipy.ndimage import map_coordinates
from scipy.ndimage.interpolation import spline_filter

# basic routines on cube files
from .cubebasics import *


class InterpolatedCube(object):
    """
    Interpolate a given cube file. The interpolation 
    makes use of scipy's map_coordinates routine.
    
    Parameters
    ----------
    cubefile : string
      Location of the cube file
    
    convert_cube_content : boolean (default: False)
      Directly passed to the read_cube routine. Determines whether input from
      the original cube is converted to e/A**3 or not. Note that this only
      works if your underlying cube file is properly formatted, i.e. if it
      writes the electronic density in units of e/voxel (FHI-aims eg. does
      not!). Consult your code documentation in case of doubt.
    
    convert_to_rs : boolean, optional (default: False)
      Converts the cube data from rho in e/A**3 to Wigner Seitz radii in a.u.
      Make sure that your cube data really is available in e/A**3 (see
      ``convert_cube_content``).
    
    PBC : boolean, optional (default: True)
      Apply periodic boundary conditions.

    shift : string, optinal, {center, *edge*}
      Controls whether the denisty values are assinged to the voxel edges or
      centers.

    order :  integer, optional (default = 3)
      The order of the spline interpolation, default is 3. The order has to
      be in the range 0-5.
    
    verbose :  boolean, optional (default = False)
        Print cube infos upon initialization.
    
    precalc_weights : boolean, optional (default = True)
        Calculate the spline weights once and for all in the constructor. This
        can save a tremendous amount of calculation time if you have several
        calls to the InterpolcatedCube instance. Basically, there is no reason
        whatsoever to set this option to False. Even for a single call to the
        instance only there is no (noticeable) lack in performance. Yet, a
        quick test on caboose yields on average for 1000 subsequent calls to
        the instance

            precalc_weights = True  : ~60 ns per call
            precalc_weights = False : ~6.5 ms per call
        
        which is a speedup of about a factor of 100!


    Call
    ----
    pos:  (3 x 1) array or an array thereof 
        Specifiying the position at which to evaluate the density. Note that
        vectorized calls to map_coordinates are highly efficient!


    Returns
    -------
    rho:  float or (Nx1) array of floats
        Density value at the specified position.
    
    --- 
    Simon P. Rittmeyer, 2014-2015 
    simon.rittmeyer(at)tum.de
    """
    
    def __init__(self, cubefile, 
                       convert_cube_content = False,
                       convert_to_rs = False, 
                       PBC = True, 
                       shift = 'edge',
                       order = 3,
                       verbose = False,
                       precalc_weights = True):
        
        self.cubefile = cubefile
        
        # read the cube file
        # convert means density in e / A**3
        full_output = read_cube(cubefile, 
                                full_output = True,
                                convert = convert_cube_content)
                                
        # conveniently map dict content to instance variables:
        #       self.atoms
        #       self.cube_data
        #       self.voxdim
        #       self.origin
        self.__dict__.update(full_output)

        if verbose:
            print(get_cube_info(self.cubefile))

        self.convert_cube_content = convert_cube_content
        self.convert_to_rs = convert_to_rs
        
        # hard coded conversion factor
        self.A2au = 1./Bohr
        
        # PBC treatment of the interpolation function
        self.PBC = PBC
     
        if self.PBC:
            self.mode = 'wrap'
        else:
            self.mode = 'constant'

        self.Q, self.Qinv = self._create_trafo_matrices(self.voxdim)

        # get the number of voxels
        self.Nx, self.Ny, self.Nz = self.cube_data.shape
        
        # get the cell
        self.cell = self.atoms.get_cell()
        
        # shifting the values
        shift = shift.lower()

        if shift == 'edge':
            self.shift = 0.0        
        else:
            self.shift = 0.5
    
        # save spline order
        self.order = order
    
        # pre-calculate the spline weights (one-time process)
        # instead of doing this with every call to map_coordinates.
        # Acc. to Joe Kington's mail here:
        # http://scipy-user.10969.n7.nabble.com/SciPy-User-3D-spline-interpolation-very-very-slow-UPDATE-td19702.html
        if precalc_weights:
            self._cube_data = spline_filter(self.cube_data, order = self.order)
            # flag for map_coordinates
            self._prefilter = False
        else:
            self._cube_data = self.cube_data
            self._prefilter = True

    def _create_trafo_matrices(self, voxdim):
        """
        We expect input positions in Cartesian coordinates. However, our cube
        is on a grid, which might be orthogonal or not but in any case not
        necessarily aligned along Cartesian axes. Hence, we need a routine that
        maps Cartesian input to a tuple of indices referring to the grid
        points. This is done via matrix transformations. If Q is the matrix
        consisting of the grid basis vectors in Cartesian coordinates, then 
        
            x = Q y
            
        where x is the position vector in Cartesian space and y is the position
        vector in ``grid space``. For this formular to work, we require Q to be
        built of the grid basis vectors columnwise! Hence, 
        
            y = Qinv x
                
        is the transformation we ultimately need. Luckily this is only 3D, thus
        the inverse is numerically basically for free. 
        
        Parameters
        ----------
        voxdim : (3x3) array
            Vectors spanning a voxel.
        """
        
        Q = self.voxdim.transpose().copy()
        Qinv = np.linalg.inv(Q)
        
        return Q, Qinv
    
    def _which_voxel(self, pos):
        """
        Routine that translates Cartesian input coordinates to grid indices.
        Note that these might as well be non-integers, as we are interpolating
        on the grid afterwards.

        Parameters
        ----------
        pos : (3x1) array or list/array of (3x1) arrays
            Input position(s) at which to evaulate the volumetric data

        Returns
        -------
        vox_index : (Nx3) array
            Grid indices as can directly be used with map_coordinates.
        """

        try:
            pos.ndim
        except AttributeError:
            pos = np.array(pos)
        # do not pos -= self.origin, as this permanently shifts pos!
        pos = pos - self.origin
        
        if pos.ndim == 1:
            vox_index = (self.Qinv.dot(pos) - self.shift).reshape((3,1))
            
        elif pos.ndim == 2:
            # if we have a list/array of positions
            vox_index = np.zeros_like(pos)
            for i, p in enumerate(pos):
                vox_index[i] = (self.Qinv.dot(p) - self.shift).flatten()
            vox_index = swapaxes(vox_index, 0, 1) 
        else:
            raise RuntimeError("Wrong position input format")
        
        return vox_index
                
    def interpolate_pos(self, pos): 
        """
        Call the interpolation function at an arbitrary position (in Cartesian
        coordinates).

        Parameters
        ----------
        pos : (3x1) array or list/array of (3x1) arrays
            Input position(s) at which to evaulate the volumetric data.
            Note that vectorized calls to map_coordinates are highly efficient,
            i.e. make use of it whenever you can!
        
        Returns
        -------
        rho : float or (Nx1) array of floats 
            Volumetric data at the given positions. Output format depends on
            class variable convert_to_rs as given upon initialization.
        """

        vox_index = self._which_voxel(pos)


        rho = map_coordinates(self._cube_data, vox_index, 
                               order = self.order, mode = self.mode,
                               prefilter = self._prefilter)
        
        try:
            rho = float(rho)
            if self.convert_to_rs:
                # rho can be negative because of numerical reasons but this is unphysical...
                if rho <= 0.:
                    return nan  

                # [rho] e/A**3 --> [rho] e/a.u.**3
                rho *= self.A2au**(-3)
                
                return (3. / (4 * np.pi * rho))**(1./3.)
            else:
                return rho
                
        except TypeError:
            # vectorized call...
            if self.convert_to_rs:
                mask = masked_less_equal(rho, 0).mask
                rho[mask] *= self.A2au**(-3)
                rho[mask] = (3. / (4 * np.pi * rho[mask]))**(1./3.)
               
                rho[np.logical_not(mask)] = nan
          
                return rho
            else:
                return rho
                

    def __call__(self, pos):
        return self.interpolate_pos(pos)

    def __str__(self):
        name =  "Interpolated Density (method = '{0:s}') from: {1:s}".format(
                 self.interpolation, self.cubefile)
        return name
        
    def get_atoms(self):
        return self.atoms


    def cut_cube(self, point, normal_vector, 
                       npoints = 100, 
                       outfile = None, 
                       write = True):
        """
        Cut the interpolated cube file. This far, this routine works fine for
        cuts (almost) orthogonal to the z axis.For other cuts, we need a more
        intelligent wat to discretize the cutting plane. Feel free to extend
        it!

        Parameters
        ----------
        point : (3 x 1) array
          Point on the cutting plane (in A).
        
        normal_vector : (3 x 1) array
          Normal vector in the cutting plane. If not normalized, the routine
          will do this for you.

        npoints : int, optional (default = 100)
          Number of points along each unit cell vector at which to evaluate
          the cut.

        outfile : string, optional (default = 'CUTTED_{cubefile}.dat')
          Outfile to write the cutted points to.
        
        write : Boolean, optional (default = True)
            Write an output file or just return the respective arrays.
        """

        # just to make sure it is actually a normalvector...
        normal_vector /= np.linalg.norm(normal_vector)
        
        def get_z(xy):
            z = 0
            for v, p, n in zip(xy, point, normal_vector):
                z += (v-p)*n
                
            z  = -1./normal_vector[2] * (z - point[2])
            return z
        
        points = []

        for i in np.linspace(0, 1, npoints):
            for j in np.linspace(0, 1, npoints):
                xy = i*self.cell[0][0:2] + j*self.cell[1][0:2]
                xyz = np.append(xy, get_z(xy))

                points.append(xyz)
        
        points = np.array(points)
        

        # disable convertion to rs... do if afterwards if you wish
        convert_to_rs = self.convert_to_rs
        self.convert_to_rs = False
        vals = self.__call__(points)
        self.convert_to_rs = convert_to_rs
        
        if write:
            if outfile == None:
                outfile = 'CUTTED_{}.dat'.format(self.cubefile)

            with open(outfile, 'w') as f:
                print('Writing cutted cube to {}'.format(outfile))

                f.write('# 2D cut through cube file: {}'.format(self.cubefile))
                f.write('\n#\n# File written on {}'.format(strftime('%c')))
                f.write('\n#\n# Point on cutting plane: {}'.format(point))
                f.write('\n# Normalvector on cutting plane: {}'.format(normal_vector))
                f.write('\n#')

                rho_str = 'rho'
                if self.convert_cube_content:
                    rho_str += ' (e/A**3)'
                else:
                    rho_str += ' (original format)'
                head = "#"
                head += '{0:>16s} {1:>17s} {2:>17s} {3:>26s}'.format('x / A', 
                                                                     'y / A', 
                                                                     'z / A', 
                                                                     rho_str)
            
                limiter = '#' + '-'*(len(head)-1)

                f.write('\n'+limiter)
                f.write('\n'+head)
                f.write('\n'+limiter)
                
                for p, v in zip(points, vals):
                    f.write('\n{1:>17.10f} {2:>17.10f} {3:>17.10f} {0:>26.10E}'.format(v, *p))

        else:
            return points, vals
            
        
