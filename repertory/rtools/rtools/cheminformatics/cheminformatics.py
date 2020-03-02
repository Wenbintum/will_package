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
Cheminformatics recipes

This is a collection of tools and functions from the wide field of
cheminformatics. Both openBabel and rdkit are used. The documentation of both
packages is far from perfect, but the tools in this module should give a good
hint on how to use other and more advanced features.

The main focus is rdkit (www.rdkit.org), since it offers more advanced
functionality than openbabel.

Author: Christoph Schober, 2015

"""
import os
from collections import namedtuple

import ase
import numpy as np
import pybel as pb
import rdkit
import rdkit.Chem.AllChem
import rdkit.Chem.Draw
from rdkit import Chem

def read(path, format="xyz", removeHs=False):
    """
    Read a molecule from a file with openbabel and convert it to a
    rdkit molecule object.

    Important: rdkit does not keep xyz coordinates, therefore
    a backconversion is not possible yet.

    Parameters
    ----------
    path : str
        The path for the file.
    format : optional, str
        The file format. Default is xyz. All openbabel formats are supported.
    removeHs : optional, bool
        If True, Hydrogen atoms are removed during the conversion.
    """
    pymol = pb.readfile(format, path).next()
    mol = pymol.write("mol")
    mol = Chem.MolFromMolBlock(mol, removeHs=removeHs)
    return mol


def get_atomic_numbers(mol):
    """
    ASE-like wrapper to get list of atomic numbers from rdkit mol
    object.

    Parameters
    ----------
    mol : rdkit.Chem.rdchem.Mol
        The rdkit molecule object.

    Returns
    -------
    atomic_num : np.array
        Array with all atomic numbers.
    """
    atomic_num = np.array([x.GetAtomicNum() for x in mol.GetAtoms()])
    return atomic_num


def convert_ase2pybel(atoms):
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
    a_str = __ase2xyz__(atoms)
    pymol = pb.readstring("xyz", a_str)

    return pymol


def init_ipython():
    """
    Init the pretty printer with ipython qtconsole or html notebook.
    """
    import rdkit.Chem.Draw.IPythonConsole
    rdkit.Chem.Draw.IPythonConsole.InstallIPythonRenderer()

def convert_ase2rdkit(atoms, removeHs=False):
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
    a_str = __ase2xyz__(atoms)
    pymol = pb.readstring("xyz", a_str)
    mol = pymol.write("mol")
    mol = Chem.MolFromMolBlock(mol, removeHs=removeHs)
    return mol


def __ase2xyz__(atoms):
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


def __automagic_conversion__(mol):
    """
    Check the format of the molecular input and convert it to
    rdkit if necessary.
    Supported inputs at the moment: ASE, any ASE-readable file.
    """
    if type(mol) is ase.atoms.Atoms:
        mol = convert_ase2rdkit(mol)
    elif isinstance(mol, str) and os.path.isfile(mol):
        mol = ase.io.read(mol)
        mol = convert_ase2rdkit(mol)
    elif type(mol) is rdkit.Chem.rdchem.Mol:
        pass
    else:
        raise RuntimeError("Unknown molecule object.\
                           Is this a rdkit / ASE object or a \
                           valid file?")
    return mol


def get_bond_connectivity(mol):
    """
    Extract the connectivity for the given molecule, i.e. all bonds in the
    molecule. This method returns only the bonds, no additional information.

    Parameters
    ----------
    mol : rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        The molecule to analyse, either as rdkit or ASE atom object.

    Returns
    -------
    bonds : list of bonds
    """
    mol = __automagic_conversion__(mol)
    raise NotImplementedError()


def draw_molecules(
    mols,
    filename,
    legends=None,
    molsPerRow=4,
    subImgSize=(
        300,
        300),
    draw_h=False):
    """
    Draw 2D images of all molecules in list on a grid.

    Parameters
    ----------
    mols : list of rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        The molecules to draw.
    filename : str
        The filename to save the picture to.
        Valid choices are pdf, svg, ps, and png.
    legends : list of str
        A list of legends for each subimage.
    molsPerRow : int
        Number of molecules drawn per row.
    subImgSize : tuple of ints (x,y)
        The size in pixel for each subimage.
    template : rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        Align the drawn molecule to the template.
        All molecules in mols must share the template.
    draw_h : boolean
        If True, draw explicit hydrogen atoms.
    """
    if draw_h is False:
        mols = [Chem.RemoveHs(mol) for mol in mols]
    else:
        mols = [Chem.AddHs(mol) for mol in mols]

    for mol in mols:
        rdkit.Chem.AllChem.Compute2DCoords(mol)
    img = rdkit.Chem.Draw.MolsToGridImage(mols, molsPerRow=molsPerRow,
                                          subImgSize=subImgSize,
                                          legends=legends)
    img.save(filename)


def draw_molecule(mol, filename, draw_h=False, template=None):
    """
    Draw a 2D image of a molecule (as could be done with e.g. ChemOffice)

    Parameters
    ----------
    mol : rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        The molecule to analyse.
    filename : str
        The filename to save the picture to.
        Valid choices are pdf, svg, ps, and png.
    template : rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        Align the drawn molecule to the template. Can be used to align
        multiple molecules with a shared template.
    """
    mol = __automagic_conversion__(mol)

    if draw_h is False:
        mol = Chem.RemoveHs(mol)

    rdkit.Chem.AllChem.Compute2DCoords(mol)
    rdkit.Chem.Draw.MolToFile(mol, filename)


def get_bond_info(mol):
    """
    Get the following attributes for each bond and atom in the
    given molecule:
        - bond type (single, double, aromatic, ...)
        - bond atoms with index and atomic number
        - atom hybridization

    Parameters
    ----------
    mol : rdkit.Chem.rdchem.Mol or ase.atoms.Atoms
        The molecule to analyse.

    Returns
    -------
    bonds : list of [namedtuple]
        A list with a namedtuple per bond with bond information.
        atomX: index of atomX
        aX_num: atomic number of atomX
        aX_hyb: hybridization of atomX ('S', 'SP2', etc)
        bond_type: Bond type as double. (3.5 = aromatic)

    Example
    -------
    >>> bonds = get_bonds(mol)
    >>> bonds[0]
    ... Bond(atom1=0,
             a1_num=6,
             a1_hyb='SP3',
             atom2=6,
             a2_num=1,
             a2_hyb='S',
             bond_type=1.0)
    >>> bonds[0].a1_hyb
    ... 'SP3'
    """
    mol = __automagic_conversion__(mol)
    bonds = list()
    bond_t = namedtuple("Bond", ["atom1",
                                 "a1_num",
                                 "a1_hyb",
                                 "atom2",
                                 "a2_num",
                                 "a2_hyb",
                                 "bond_type"])

    bond_gen = mol.GetBonds()

    for num, bond in enumerate(bond_gen):
        a_start = bond.GetBeginAtom()
        a_end = bond.GetEndAtom()
        try:
            a1_hyb = a_start.GetHybridization().name
        except AttributeError:
            a1_hyb = "S"
        try:
            a2_hyb = a_end.GetHybridization().name
        except AttributeError:
            a2_hyb = "S"

        b = bond_t(atom1=a_start.GetIdx(),
                   a1_num=a_start.GetAtomicNum(),
                   a1_hyb=a1_hyb,
                   atom2=a_end.GetIdx(),
                   a2_num=a_end.GetAtomicNum(),
                   a2_hyb=a2_hyb,
                   bond_type=bond.GetBondTypeAsDouble())

        bonds.append(b)

    return bonds
