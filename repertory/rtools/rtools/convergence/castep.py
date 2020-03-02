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
CASTEP Interface to the `Convergence` parent class.

This far there is support for kpoint, cutoff and vauum variation. Observable is
always the electronic energy, no geometric information. Of course you can
calculate e.g. adsorption energies from these energies.

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

from __future__ import print_function

import os
import numpy as np

from ase.io.castep import read_castep

from rtools.submitagents.arthur.castep import submit
from rtools.helpers.castephelpers import read_energy

from rtools.convergence import Convergence
from rtools.filesys import mkdir
from rtools.misc import get_close_matches

class Castep(Convergence):
    """
    Class that provides a `Convergence` interface to the CASTEP DFT code.
    The electronic energy is the only observable supported this far.
    There is some further rudimentary support of fcc lattice constants.

    The constructor is unchanged from the parent class:


    Initialization
    --------------
    ''seed''
        string
        Common seed for all caluclations. Usualy, this will be your system
        identifyer.

    ''get_atoms''
        function
        Function which returns an ASE atoms object that specifies the geometry
        of the system to be investigated. This Function must not require any
        arguments. Use lambda function in case to need to set some defaults.

    ''get_calc''
        function
        Function that returns the readily parametrized CASTEP-ASE calculator.
        As for `get_atoms`, this function must not require any additional
        arguments.

    ''hdf5file''
        string, optional (default: 'database.h5')
        Path to a HDF5 database in which the results of the convergence tests
        may be stored. Defaults to `database.h5`. Note that HDF5 support
        requires PyTables and Pandas!

    ''base_dir''
        string, optional (default: '.')
        Base directory under which all further (sub)folder for all calculations
        are created. Defaults to the current working directory.

    ''get_slab''
        function, optional
        Function which returns the clean slab (without adsorbate) of a surface
        system. This is only required for checking the vacuum spacing of an
        adsorbed system, when the target quantity is the respective adsorption
        energy.

    ''add_adsorbate''
        function, optional
        Parametrized add_adsorbate function from ase.lattice.surface that the
        required adsorbate to the slab as obtained from `get_slab()`. The only
        argument of this function is the atoms object describing the clean
        slab.

    ---
    Simon P. Rittmeyer, 2015
    simon.rittmeyer(at)tum.de
    """

    # additional pseudopotential alias
    _pp_alias = {'OTF_USPP_v5' : ['OTF_USPP_5.0-7.0', 'OTF_5', 'OTF_USPP_5'],
                 'OTF_USPP_v8' : ['OTF_USPP_8.0', 'OTF_8', 'OTF_USPP_8'],
                 'CL_USPP'     : ['CL'],
                 'MS_USPP'     : ['MS'],
                 'CS09_NCPP'   : ['NCPP', 'CS09NCPP'],
                 'OTF_USPP_C9' : ['USPP_C9', 'C9', 'C9_USPP', 'C9_USPP_OTF'],
                 'OTF_USPP_C18': ['USPP_C18', 'C18', 'C18_USPP', 'C18_USPP_OTF'],
                 'GBRV_v14'   : ['GBRV_v1.4', 'gbrv_1.4', 'GBRV1.4', 'GBRV_1.4'],
                 'GBRV_v15'   : ['GBRV_v1.5', 'GBRV', 'gbrv_1.5', 'gbrv', 'GBRV1.5', 'GBRV_1.5']
                 }

    # why should we need to add it explicitly...?
    for k in _pp_alias:
        _pp_alias[k].append(k)

    _all_pp_alias = []
    for alias in _pp_alias.values():
        _all_pp_alias += alias

    def _normalize_pseudopotential(self, pp):
        """
        Function that normalizes pseudopotentials to be HDF5 compatible.
        There will *not* be any string normalization with `_normalize_str()`

        Arguments
        ---------
        ''pp''
            string
            Pseudopotential name

        Returns
        -------
        ''normpp''
            string
            Pseudopotential name which is compatible with HDF5 files.

        Raises
        ------
        `NotImplementedError` if pseudopotential is not known.
        """
        found = False
        for ipp, alias in self._pp_alias.items():
            if pp in alias:
                normpp = ipp
                found = True
        if found:
            return normpp
        else:
            err_msg = "Unknown pseudopotential: ``{}''".format(pp)
            print(err_msg)
            print(get_close_matches(pp, self._pp_alias))
            raise NotImplementedError(err_msg)

    def _prepare(self, task, var,
                      # just a dummy, no longe required with latest ase
                      pspot_suffix = 'OTF',
                      ):
        """
        Function that wraps all necessary tasks to run several calculations.
        Does not actually run the calculation.

        Arguments
        ---------
        ''task''
            string
            Actual task to carry out. Will be filtered via `_normalize_task()`.
            Currently available since implemented are
                * 'kpoints'
                * 'cutoff'
                * 'vacuum' / 'vacuumwithadsorbate'

        ''var''
            str/generic
            Values that the varied parameter should correspond to. For
            `cutoff` and `vacuum`, these may be floats or integers, for
            `kpoints` we require strings like 'X Y Z', which are directly
            passed to the `KPOINTS_MP_GRID` variable in the `*.cell` file.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.


        Returns
        -------
        ''atoms''
            readily prepared atoms object.

        ''iseed''
            The iseed of the prepared calculation

        ''idir''
            The idir of the prepared calculation.
        """
        # get the indivial variables
        iseed = self.get_iseed(var  = var,
                               task = task)
        idir = self.get_idir(var = var,
                             task = task)

        # create folder if necessary
        # if results exist: skip!
        if mkdir(idir, backup_existing = False,
                       purge_existing = False,
                       verbose = False):
            pass
        else:
            return [None]*3

        # get the calculator and set label and dir
        calc = self.get_calc()
        calc._label = iseed
        calc._directory = idir

        # get the atoms
        atoms = self.get_atoms()

        if task == 'kpoints':
            # set the k point mesh
            calc.cell.kpoints_mp_grid = var

        elif task == 'kpointspacing':
            calc.cell.kpoints_mp_spacing = float(var)

        elif task == 'cutoff':
            # set the cutoff
            calc.cut_off_energy = int(var)

        elif task == 'vacuum':
            # resize the separating distance
            atoms.center(vacuum = var/2., axis = 2)

        elif task == 'vacuumwithadsorbate':
            atoms = self._get_slab()
            atoms.center(vacuum = var/2., axis = 2)
            self._add_adsorbate(atoms)

        # set the calculator
        atoms.set_calculator(calc)

        # we need it hard code it here...
        # calc.set_pspot(pspot = pspot_suffix)

        atoms.calc.prepare_input_files()

        return atoms, iseed, idir

    def calculate(self, task, var_list,
                  pspot_suffix = 'OTF',
                  **kwargs):
        """
        Function that wraps all necessary tasks to run several calculations.

        Arguments
        ---------
        ''task''
            string
            Actual task to carry out. Will be filtered via `_normalize_task()`.
            Currently available since implemented are
                * 'kpoints'
                * 'kpointspacing'
                * 'cutoff'
                * 'vacuum' / 'vacuumwithadsorbate'

        ''var_list''
            list
            List of values that the varied parameter should correspond to. For
            `cutoff` and `vacuum`, these may be floats or integers, for
            `kpoints` we require strings like 'X Y Z', which are directly
            passed to the `KPOINTS_MP_GRID` variable in the `*.cell` file.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''**kwargs''
            are directly passed to the `submit()` function from
            rtools.submitagents.arthur.castep.

        Returns
        -------
        None
        """
        task = self._normalize_task(task, supset = False)
        for var in var_list:
            atoms, iseed, idir = self._prepare(task=task, var=var, pspot_suffix=pspot_suffix)
            if not atoms: continue
            kwargs['result_dir'] = 'results'

            submit(seed = iseed,
                   job_dir = idir,
                   **kwargs)

    def calculate_ase(self, task, var_list,
                      pspot_suffix = 'OTF',
                      dryrun = False,
                      ):
        """
        Function that wraps all necessary tasks to run several calculations
        thorugh the ase calulator.

        Arguments
        ---------
        ''task''
            string
            Actual task to carry out. Will be filtered via `_normalize_task()`.
            Currently available since implemented are
                * 'kpoints'
                * 'cutoff'
                * 'vacuum' / 'vacuumwithadsorbate'

        ''var_list''
            list
            List of values that the varied parameter should correspond to. For
            `cutoff` and `vacuum`, these may be floats or integers, for
            `kpoints` we require strings like 'X Y Z', which are directly
            passed to the `KPOINTS_MP_GRID` variable in the `*.cell` file.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''dryrun''
            boolean, optional (default=False)
            Only prepare input files, do not run a calculation.

        Returns
        -------
        None
        """
        task = self._normalize_task(task, supset = False)
        for var in var_list:
            atoms, iseed, idir = self._prepare(task=task, var=var, pspot_suffix=pspot_suffix)
            if not atoms: continue

            # calculate in results dirctory directly
            atoms.calc._directory = os.path.join(idir, 'results')

            if dryrun:
                atoms.calc._prepare_input_only = True

            print('Running {}\n\tdirectory: {}'.format(iseed, idir))
            E = atoms.get_potential_energy()
            if dryrun:
                print('\t*dryrun*')
            else:
                print('\tE = {}'.format(E))


    def read_energy(self, task):
        """
        Function that parses walks a given directory and parses the respective
        output files.

        Arguments
        ---------
        ''task''
            string
            Task that should be analyzed. Will be filtered via
            `_normalize_task()`. By specifying the `task` the routine knows,
            where the respective calculations are stored (hard coded in the
            parent class!).

        Returns
        -------
        ''data''
            list
            List of tuples
                (var, energy, exists, finished, converged)
            of type
                (str, float, bool, bool, bool).
            Each calculation corresponds to a tuple.
        """
        data = []
        result_dir = 'results'

        task = self._normalize_task(task)

        calc_dir = os.path.join(self.base_dir, task)
        for path, dirs, files in os.walk(calc_dir):
            if result_dir in dirs:
                var = os.path.basename(path).split('-')[0]
                E = np.nan
                existing = False
                finished = False
                converged = False
                for f in os.listdir(os.path.join(path, result_dir)):
                    if f.endswith('.castep'):
                        existing = True
                        _, finished, converged = read_energy(os.path.join(path, result_dir, f), get_status = True)

                        if finished:
                            atoms = read_castep(os.path.join(path, result_dir, f))
                            E_corr = atoms.calc.get_total_energy_corrected()
                            E = atoms.get_potential_energy()
                        #print(E, E_corr)

                data.append((var, E, existing, finished, converged))
        return data

    def read_forces(self, task):
        """
        Function that parses walks a given directory and parses the respective
        output files.

        Arguments
        ---------
        ''task''
            string
            Task that should be analyzed. Will be filtered via
            `_normalize_task()`. By specifying the `task` the routine knows,
            where the respective calculations are stored (hard coded in the
            parent class!).

        Returns
        -------
        ''data''
            list
            List of tuples
                (var, forces, exists, finished, converged)
            of type
                (str, np.array, bool, bool, bool).
            Each calculation corresponds to a tuple.
        """
        data = []
        result_dir = 'results'

        task = self._normalize_task(task)

        calc_dir = os.path.join(self.base_dir, task)
        for path, dirs, files in os.walk(calc_dir):
            if result_dir in dirs:
                var = os.path.basename(path).split('-')[0]
                forces = np.ones((1,1,))*np.nan
                existing = False
                finished = False
                converged = False
                for f in os.listdir(os.path.join(path, result_dir)):
                    if f.endswith('.castep'):
                        existing = True
                        _, finished, converged = read_energy(os.path.join(path, result_dir, f), get_status = True)

                        if finished:
                            atoms = read_castep(os.path.join(path, result_dir, f))
                            forces = atoms.calc.get_forces()
                        #print(E, E_corr)
                        else:
                            forces = np.ones_like(atoms.positions) * np.nan
                data.append((var, forces, existing, finished, converged))
        return data

    def read_stress(self, task):
        """
        Function that parses walks a given directory and parses the respective
        output files.

        Arguments
        ---------
        ''task''
            string
            Task that should be analyzed. Will be filtered via
            `_normalize_task()`. By specifying the `task` the routine knows,
            where the respective calculations are stored (hard coded in the
            parent class!).

        Returns
        -------
        ''data''
            list
            List of tuples
                (var, stress, exists, finished, converged)
            of type
                (str, np.array, bool, bool, bool).
            Each calculation corresponds to a tuple.
        """
        data = []
        result_dir = 'results'

        task = self._normalize_task(task)

        calc_dir = os.path.join(self.base_dir, task)
        for path, dirs, files in os.walk(calc_dir):
            if result_dir in dirs:
                var = os.path.basename(path).split('-')[0]
                s = np.ones((3,3))*np.nan
                existing = False
                finished = False
                converged = False
                for f in os.listdir(os.path.join(path, result_dir)):
                    if f.endswith('.castep'):
                        existing = True
                        _, finished, converged = read_energy(os.path.join(path, result_dir, f), get_status = True)
                        if finished:
                            atoms = read_castep(os.path.join(path, result_dir, f))
                            s = atoms.calc.get_stress()
                        #print(E, E_corr)
                data.append((var, s, existing, finished, converged))
        return data

    def read_fcc_lattice_constant(self, task):
        """
        Function that parses walks a given directory and parses the respective
        output files.

        Arguments
        ---------
        ''task''
            string
            Task that should be analyzed. Will be filtered via
            `_normalize_task()`. By specifying the `task` the routine knows,
            where the respective calculations are stored (hard coded in the
            parent class!).

        Returns
        -------
        ''data''
            list
            List of tuples
                (var, d, exists, finished, converged)
            of type
                (str, float, bool, bool, bool).
            Each calculation corresponds to a tuple.
        """

        data = []
        result_dir = 'results'

        variable = self._normalize_task(task)

        calc_dir = os.path.join(self.base_dir, variable)
        for path, dirs, files in os.walk(calc_dir):
            if result_dir in dirs:
                var = os.path.basename(path).split('-')[0]
                d = np.nan
                existing = False
                finished = False
                converged = False
                for f in os.listdir(os.path.join(path, result_dir)):
                    if f.endswith('.castep'):
                        existing = True
                        _, finished, converged = read_energy(os.path.join(path, result_dir, f),
                                                             get_status = True)
                        atoms = read_castep(os.path.join(path, result_dir, f))[0]
                        d = sum(atoms.cell[0])
                data.append((var, d, existing, finished, converged))
        return data

    def write_fcc_lattice_constant_text(self, task):
        """
        Routine that wraps reading and writing to clear text.

        Arguments
        ---------
        ''task''
            string
            Task to be analyzed. Will be filtered via `_normalize_task()`.

        Returns
        -------
        ''data''
            list
            List of tuples
                (var, value, exists, finished, converged)
            of type
                (str, float, bool, bool, bool).
            Each calculation corresponds to a tuple.
        """

        task = self._normalize_task(task)
        data = self.read_fcc_lattice_constant(task)
        self.write_data(data = data,
                         task = task,
                         observable = 'fcclatticeconstant')


# just a convenience wrapper (staticmethods would break to much workflow)
__conv = Castep(None, None, None)
def normalize_pseudopotential(pp):
    return __conv._normalize_pseudopotential(pp)
