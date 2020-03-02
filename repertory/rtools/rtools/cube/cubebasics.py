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

# linear algebra
import numpy as np

# ASE functionality
from ase.atoms import Atoms
from ase.units import Bohr

def read_cube(fileobj, read_data = False, full_output = False, convert = False,
                       program = None, verbose = False):
    """
    This is a tweaked version of the cubefile reader as found in the
    ase.io.cube module, since the latter cannot deal with the different ways to
    handle periodic boundaries conditions, different programs apply. See `Notes`
    below for details.

    In contrast to ase.io.cube.read_cube(), this function returns an additional
    array specifying the dimensions (in Angstrom) of the respective voxels the
    cube is build of, if read_data = True.

    NOTE: This functionality will be ported back to ASE. It will remain as a
    legacy here in rtools but no futher development is done!

    Parameters
    ----------
    fileobj : string
        Location to the cubefile.

    read_data : boolean, optional (default = False)
        If set true, the actual cube file content, i.e. an array
        containing the electronic density on a grid and the dimensions
        of the corresponding voxels are returned.

    full_output : boolean, optional (default = False)
        If set True, a dictionary will be returned with the following keys:
            * 'atoms'     : Atoms object containing the actual system, i.e.
                            positions, atom types and cell dimensions.
            * 'cube_data' : (Nx x Ny x Nz) array containg the electronic density
                            values (for units see convert argument) from the cube
                            file, where Nx, Ny, and Nz are the number of voxels in
                            the respective direction.
            * 'voxdim'    : (3 x 3 x 3) array containg the length of each voxel
                            along each direction of the coordinate system in
                            Angstrom.
            * 'origin'    : (3x1) array, specifying the cube_data origin. May be
                            different to zero for some programs (e.g. FHI-aims).

        Note that full_output suppresses any other output, ie. there will be no
        atoms or data object returned besides from the one in the dictionary.

    convert : boolean, optional (default = False)
        If set true, the electronic density is returned in units of
        e/Angstrom**3 and the voxel dimensions are returned in Angstrom.
        If set False, there will be no conversion whatsoever of the
        input data, i.e. e/voxel.

    program : string, optional ({'castep', 'FHI-aims'})
        Program that wrote the actual cube file. this helps to avoid for instance
        issues with the way PBC are handled within the cube file, or how to treat
        the `origin` of the cube_datae in FHI-aims. If None is given, the routine
        tries to catch the program type from the comment line in the cube file.

        Choosing `castep` follows the PBC conventions that first and last voxel
        along a direction are mirror images, thus the last voxel is to be removed.
        However, the routine tries to catch castep files from the second comment
        line.

    verbose : boolean, optional (default = True)
        Print some more information to stdout.

    Returns
    -------
    atoms : atoms object
        Atoms object containing the actual system, i.e. positions, atom types and
        cell dimensions.

    data : numpy array, optional
        (Nx x Ny x Nz) array containg the electronic density values (for units see
        convert argument) from the cube file, where Nx, Ny, and Nz are the number of
        voxels in the respective direction.

    full_output : dictionary, optional
        Dictionary holding the entire output. The respective keys are specified in
        the `Parameters` section.


    Notes
    -----

    Periodic boundary conditions (PBC) and cube files are somewhat difficult to
    handle. They were not made to handle PBC, however, if you want to visualize
    periodic volumetric data, you need to incorporate it. See e.g. this link:

        http://www.xcrysden.org/doc/XSF.html#__toc__11

    To my experience, most codes apply a *general grid* to write cube files.
    However, CASTEP for instance uses a *periodic grid* in this lingo. This
    means, that every last entry along an axis is redundant.

    ---
    Simon P. Rittmeyer, 2015
    simon.rittmeyer(at)tum.de
    """

    programs = ['FHI-aims', 'castep', None]
    if not program in programs:
        program = None

    # Bohr --> Angstrom conversion (hard coded from ASE)
    #Bohr = 0.5291772575069165

    # assign second variable as we might need to change it...
    convert_to_angstrom = Bohr
    convert_voxel_dimensions = Bohr

    _close = False

    if isinstance(fileobj, str):
        fname = fileobj.lower()
        if fname.endswith('.gz'):
            import gzip
            _close = True
            fileobj = gzip.open(fileobj)
        elif fname.endswith('.bz2'):
            import bz2
            fileobj = bz2.BZ2File(fileobj)
        else:
            _close = True
            fileobj = open(fileobj)

    readline = fileobj.readline

    line = readline()

    # The first comment line *CAN* contain information on the axes
    # But this is by far not the case for all programs
    axes = []
    try:
        axes = ['XYZ'.index(s[0]) for s in line.split()[2::3]]
    except ValueError:
        pass
    if axes == []:
        axes = [0, 1, 2]

    # AIMS cubes are identified via the first line
    if 'CUBE FILE written by FHI-AIMS' in line:
        program = 'FHI-aims'
    elif 'cube file from ase' in line:
        program = 'ase'

    # castep2cube files have a specific comment in the second line...
    line = readline()
    if 'castep' in line:
        program = 'castep'

    if not program is None:
        if verbose:
            print('read_cube identified program: {}'.format(program))

    # Third line contains actual system information
    line = readline().split()
    natoms = int(line[0])

    # origin around which the volumetric data is centered (at least in FHI aims)
    origin = np.array([float(x)*Bohr for x in line[1::]])

    # additionally we want the voxel dimensions stored and returned in Angstrom
    voxdim = np.empty((3, 3))
    cell = np.empty((3, 3))
    shape = []

    # the upcoming three lines contain the cell information
    for i in range(3):
        n, x, y, z = [float(s) for s in readline().split()]

        # if n is negative, then units are Angstrom, else they are Bohr!
        # see: http://paulbourke.net/dataformats/cube/
        if n < 0:
            convert_to_angstrom = 1.

        shape.append(int(n))

        # different PBC treatment in castep, basically the last voxel row is
        # identical to the first one
        if program == 'castep':
            cell[i] = (n-1) * convert_to_angstrom * np.array([x, y, z])
        else:
            cell[i] = (n) * convert_to_angstrom * np.array([x, y, z])

        # voxel dimensions in Angstrom!
        voxdim[i] = np.array([x,y,z]) * convert_to_angstrom

    numbers = np.empty(natoms, int)
    positions = np.empty((natoms, 3))
    for i in range(natoms):
        line = readline().split()
        numbers[i] = int(line[0])
        positions[i] = [float(s) for s in line[2:]]

    # positions in angstrom for the atoms object
    #positions *= convert_to_angstrom
    # As far as I understood http://paulbourke.net/dataformats/cube/
    # positions are always in Bohr
    positions *= Bohr

    # CASTEP will always have PBC, although the cube format does not
    # contain this kind of information
    if program == 'castep':
        pbc = True
    else:
        pbc = False

    atoms = Atoms(numbers=numbers, positions=positions, cell=cell, pbc = pbc)

    # voxel volume is the triple product of the lattice vectors (in Angstrom**3)
    voxvol=abs(np.dot(voxdim[0], np.cross(voxdim[1],voxdim[2])))


    # prepare the output
    if full_output or read_data:
        # reshape the data
        data = np.array([float(s) for s in fileobj.read().split()]).reshape(shape)
        if axes != [0, 1, 2]:
            data = data.transpose(axes).copy()

        # close the file if necessary
        if _close:
            fileobj.close()

        # convert values from e/voxel to e/A**3
        if convert:
            if not program == 'FHI-aims':
                # FHI aims is already in Angstrom**-3
                data *= 1./voxvol

        if program == 'castep':
            # Due to the PBC applied in castep2cube, the last entry along each
            # dimension equals the very first one.
            # In addtion to the cube data and the atoms object, return the voxel
            # dimensions (elsewhise the data object is more or less useless).
            data = data[:-1,:-1,:-1]


        if full_output:
            full_output = {'atoms'     : atoms,
                           'cube_data' : data,
                           'voxdim'    : voxdim,
                           'origin'    : origin}
            return full_output

        if read_data:
            return atoms, data

    else:
        # close the file if necessary
        if _close:
            fileobj.close()

        return atoms


def write_cube(fileobj, atoms, data=None, origin = None, comment=None):
    """
    Function to write a cube file to a given fileobj.

    This routine is copied from ase.io.cube and slightly modified.

    Parameters
    ----------
    fileobj : string or pointer to open file
        File to which output is written.

    atoms : ase atoms object
        Atoms object specifying the atomic configuration.

    data : 3dim numpy array, optional (default = None)
        Array containing volumetric data as e.g. electronic density

    origin : 3-tuple
        Origin of the volumetric data (units: Angstrom)

    comment : string, optional (default = None)
        Comment for the first line of the cube file.
    """
    _close = False

    if isinstance(fileobj, str):
        _close = True
        fileobj = open(fileobj, 'w')

    if isinstance(atoms, list):
        if len(atoms) > 1:
            raise ValueError('Can only write one configuration '
                             'to a cube file!')
        atoms = atoms[0]

    if data is None:
        data = np.ones((2, 2, 2))
    data = np.asarray(data)

    if data.dtype == complex:
        data = np.abs(data)

    if comment is None:
        fileobj.write('cube file from ase, written on %s'%timestrftime('%c'))
    else:
        comment = comment.strip()
        fileobj.write(comment)

    fileobj.write('\nOUTER LOOP: X, MIDDLE LOOP: Y, INNER LOOP: Z\n')

    cell = atoms.get_cell()
    shape = np.array(data.shape)

    if origin is None:
        corner = np.zeros(3)
        for i in range(3):
            if shape[i] % 2 == 1:
                shape[i] += 1
                corner += cell[i] / shape[i] / Bohr
    else:
        corner = [float(i)/Bohr for i in origin]

    fileobj.write('%5d%12.6f%12.6f%12.6f\n' % (len(atoms), corner[0],
                                               corner[1], corner[2]))

    for i in range(3):
        n = data.shape[i]
        d = cell[i] / shape[i] / Bohr
        fileobj.write('%5d%12.6f%12.6f%12.6f\n' % (n, d[0], d[1], d[2]))

    positions = atoms.get_positions() / Bohr
    numbers = atoms.get_atomic_numbers()
    for Z, (x, y, z) in zip(numbers, positions):
        fileobj.write('%5d%12.6f%12.6f%12.6f%12.6f\n' % (Z, 0.0, x, y, z))

    data.tofile(fileobj, sep='\n', format='%e')

    if _close:
        fileobj.close()


def get_cube_info(cubefile):
    """
    Routine that extracts some information from a cube file.

    Parameters
    ----------
    ''cubefile''
        string
        Path to the cube file

    Returns
    -------
    Formated string with cube information

    ---
    Simon P. Rittmeyer, 2014
    simon.rittmeyer(at)tum.de
    """
    # read the cube file:
    cube = read_cube(cubefile, full_output = True,
                     convert = False)

    atoms = cube['atoms']
    data = cube['cube_data']
    voxdim = cube['voxdim']

    limiter = '-'*80

    info  = limiter
    info += '\nInformation on cubefile:\n\t{}'.format(cubefile)
    info += '\n'+limiter

    # General info
    info += '\nTotal number of electrons in cube : {0:<10.6f}'.format(sum(data.flatten()))
    info += '\nTotal number of atoms in cube     : {0:<d}'.format(len(atoms))
    info += '\n'+limiter

    # cube information
    info += '\nCubefile consists of {0:d} x {1:d} x {2:d} voxels'.format(*data.shape)
    info += '\nVoxel vectors (in A):'
    for v in voxdim:
        info += '\n\t{0:>10.6f} {1:>10.6f} {2:>10.6f}'.format(*v)
    info += '\n'+limiter

    # cell information
    info += '\nUnderlying cell (unit vectors in A):'
    for v in atoms.get_cell():
        info += '\n\t{0:>10.6f} {1:>10.6f} {2:>10.6f}'.format(*v)

    # atoms information
    info += '\nAtoms in cell (positions in A):'
    for name, pos in zip(atoms.get_chemical_symbols(), atoms.get_positions()):
        info += '\n\t{0:2s} {1:>10.6f} {2:>10.6f} {3:>10.6f}'.format(name, *pos)
    info += '\n'+limiter

    return info

