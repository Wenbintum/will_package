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
Converters

This is a collection of useful converter functions between different
codes, e.h. ase2rdkit or ase2pybel.

Author: Christoph Schober, 2015

"""
import StringIO
import ase
import ase.io

try:
    import pybel as pb
except ImportError:
    print('pybel is not installed, related methods will fail.')

try:
    from rdkit import Chem
except ImportError:
    print('rdkit is not installed, related methods will fail.')


def ase2pybel(atoms):
    """
    Convert an ASE atoms object to pybel (openBabel) molecule.
    The ordering of the Atoms is identical.

    Parameters
    ----------
    atoms : ase.Atoms
        The ASE atoms object

    Returns
    -------
    pymol :
        The pybel molecule.
    """
    a_str = ase2xyz(atoms)
    pymol = pb.readstring("xyz", a_str)

    return pymol


def ase2rdkit(atoms, removeHs=False):
    """
    Convert an ASE atoms object to rdkit molecule.
    The ordering of the Atoms is identical.


    Important: Implemented only for clusters, not PBC!
    rdkit does not keep xyz coordinates, therefore
    a backconversion is not possible yet.

    Parameters
    ----------
    atoms : ase.Atoms
        The ASE atoms object
    removeHs : Bool
        If True, remove all H atoms from molecule.

    Returns
    -------
    mol : rdkit.Chem.rdchem.Mol
        The rdkit molecule object.
    """
    a_str = ase2xyz(atoms)
    pymol = pb.readstring("xyz", a_str)
    mol = pymol.write("mol")
    mol = Chem.MolFromMolBlock(mol, removeHs=removeHs)
    return mol


def ase2xyz(atoms):
    """
    Prepare a XYZ string from an ASE atoms object.
    """
    # Implementation detail: If PBC should be implemented, the
    # write to xyz needs to be changed to include cell etc.
    if any(atoms.get_pbc()):
        raise RuntimeError("Detected PBCs. Not supported (yet)!")
    num_atoms = len(atoms)
    types = atoms.get_chemical_symbols()
    all_atoms = zip(types, atoms.get_positions())
    a_str = str(num_atoms) + "\n" + "\n"
    for atom in all_atoms:
        a_str += atom[0] + " " + " ".join([str(x) for x in atom[1]]) + "\n"
    return a_str


def xyz2ase(xyz_str):
    """
    Convert a xyz file to an ASE atoms object via in-memory file (StringIO).
    """
    xyzfile = StringIO.StringIO()
    xyzfile.write(xyz_str)
    mol = ase.io.read(xyzfile, format="xyz")
    return mol
