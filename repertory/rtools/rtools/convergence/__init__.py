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
Convergence test suite.

This is just the base class, it has to be interfaced to the particular
electronic structure code you are using. Please, do not add any code specific
routines to this class but rather make use of the power of object oriented
programming. Add routines only if they are generic enough to work with more
than one code. There is a working interface to the CASTEP code.

This test suite heavily relies on ASE routine. It is (this far) geared towards
surface science investigations, i.e. there are checks for vauum spacing, basis
set cutoff (plane waves this far only), and k-point grid as variables. But it
should be comparatively easy to extend it to other tasks.

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

from __future__ import print_function

import re
import os
import time
import argparse

import numpy as np

from rtools.misc import get_close_matches
from rtools.misc import get_cmd_args

try:
    import pandas as pd
    import tables
    from rtools.helpers.pandashelpers import create_pandas_dataframe
    from rtools.helpers.pandashelpers import create_generic_pandas_dataframe
    from rtools.helpers.pandashelpers import update_hdf_node
    print('Pandas (+HDF5) support available')
except ImportError:
    print('Pandas (+HDF5) support *NOT* available')


class Convergence(object):
    """
    Convergence test suite.

    This is just the base class, it has to be interfaced to the particular
    electronic structure code you are using. Please, do not add any code
    specific routines to this class but rather make use of the power of object
    oriented programming. Add routines only if they are generic enough to work
    with more than one code.

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
        Function that returns the respective ASE calculator. As for
        `get_atoms`, this function must not require any additional arguments.

    ''hdf5file''
        string, optional
        Path to a HDF5 database in which the results of the convergence tests
        may be stored. Note that HDF5 support requires PyTables and Pandas!

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
    # task aliases
    _task_alias = {'kpoints'             : ['kpoints', 'kgrid', 'kmesh', 'kpoint'],
                   'cutoff'              : ['cutoff', 'cutoffenergy'],
                   'vacuum'              : ['vacuum', 'spacing', 'separation'],
                   'vacuumwithadsorbate' : ['vacuumwithadsorbate', 'spacingwithadsorbate', 'separationwithadsorbate'],
                   'kpointspacing'       : ['kpointspacing', 'kspacing', 'kpointsspacing', 'kpointsseparation']
                   }

    _all_task_alias = []
    for alias in _task_alias.values():
        _all_task_alias += alias

    # observable alias
    _obs_alias = {'energy'              : ['energies', 'energy', 'E'],
                  'fcclatticeconstant'  : ['fccd', 'fcclatticeconstant', 'fcca', 'fcc'],
                  'forces'  : ['forces', 'force', 'F'],
                  'stress'  : ['stress', 'stresstensor', 'sigma']
                  }

    _all_obs_alias = []
    for alias in _obs_alias.values():
        _all_obs_alias += alias


    _logo = r"""
-------------------------------------------------------------------------------
              ____
             / ___|___  _ ____   _____ _ __ __ _  ___ _ __   ___ ___
            | |   / _ \| '_ \ \ / / _ \ '__/ _` |/ _ \ '_ \ / __/ _ \
            | |__| (_) | | | \ V /  __/ | | (_| |  __/ | | | (_|  __/
             \____\___/|_| |_|\_/ \___|_|  \__, |\___|_| |_|\___\___|
                                           |___/

                        Simon P. Rittmeyer, TUM, 2015
                          simon.rittmeyer(at)tum.de
-------------------------------------------------------------------------------
"""[1:-1]

    _print_logo = True

    def __init__(self,
                 seed,
                 get_atoms,
                 get_calc,
                 hdf5file = None,
                 base_dir = None,
                 # for adsorption systems only
                 get_slab = None,
                 add_adsorbate = None):

        if Convergence._print_logo:
            print(self._logo)
            Convergence._print_logo = False


        # These two functions are system and calculator specific!
        self.get_atoms = get_atoms
        self.get_calc = get_calc

        # seed is mandatory
        self.seed = seed

        if base_dir == None:
            self.base_dir = os.getcwd()
        else:
            self.base_dir = base_dir

        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        if hdf5file != None:
            self._hdf5file = hdf5file
            try:
                self.store = pd.HDFStore(self._hdf5file)
            except AttributeError:
                pass

        # Only for adsorption systems
        self._get_slab = get_slab
        self._add_adsorbate = add_adsorbate


    def _normalize_str(self, string, pattern = r'[\s\-_\.]*'):
        """
        Normalize a given string. By removing all whitespaces, dots (.),
        underscores (_) and hyphens (-), and consequently converting to lower
        case letters. This allows to compare strings on a more reliable basis.

        Arguments
        ---------
        ''string''
            string
            String that is to be normalized.

        ''pattern''
            raw-string, optional (default : r'[\s\-_\.]*')
            Regex pattern that specifies every character that is to be deleted
            from the original string.

        Returns
        -------
        ''string''
            string
            Normalized string.
        """
        return re.sub(pattern, '', string).lower()


    def _normalize_task(self, task, supset = True):
        """
        Normalize a task. This is useful to catch typos or handle synonyms for
        same tasks. This routine first normalizes the task string and
        consquently checks whether the normalized string is in any of the
        class-internal alias lists. If so, a unique normalized task identifyer
        is returned, which can be compared to.

        Feel free to extend this routine according to your needs.

        Arguments
        ---------
        ''task''
            string
            String specifying the task.

        ''supset''
            Boolean, optional (default : True)
            Some tasks can be grouped. If `supset = True` the routine will
            return the same task for different subtasks. For instance, `vacuum`
            and `vacuumwithadsorbate` are intrinsically different tasks, but
            with `supset = True` the routine will return `vacuum` in both
            cases.

        Returns
        -------
        ''normtask''
            string
            Normalized string specifying the task.

        Raises
        ------
        `NotImplementedError` if task is not known.
        """
        task = self._normalize_str(task)
        found = False
        for itask, alias in self._task_alias.items():
            if task in alias:
                found = True
                normtask = itask
                break
        if found:
            # filter the supset
            if normtask in ['vacuumwithadsorbate']:
                if supset:
                    normtask = 'vacuum'
            return normtask
        else:
            err_msg = "Unknown task: ``{}''".format(task)
            print(err_msg)
            print(get_close_matches(task, self._all_task_alias))
            raise NotImplementedError(err_msg)

    def _normalize_observable(self, obs):
        """
        Normalize an observable. Again, this is for comparison reason. The
        routine compares against the class-internal observable alias lists.

        Arguments
        ---------
        ''obs''
            string
            String specifying the observable.

        Returns
        -------
        ''normobs''
            string
            Normalized string specifying the observable.

        Raises
        ------
        `NotImplementedError` if observable is unknown.
        """
        obs = self._normalize_str(obs)
        found = False
        for iobs, alias in self._obs_alias.items():
            if obs in alias:
                found = True
                normobs = iobs
                break
        if found:
            return normobs
        else:
            err_msg = "Unknown observable: ``{}''".format(obs)
            print(err_msg)
            print(get_close_matches(obs, self._all_obs_alias))
            raise NotImplementedError(err_msg)


    def get_iseed(self, var, task):
        """
        Create an individual seed for each calculation based on general seed,
        task and value of the veried parameter.

        Feel free to add whatever is needed for other tasks, but try to stick
        with the overall functionality.

        Arguments
        ---------
        ''var''
            float/int/string
            Current value of the variable, ie. the parameter that is varied.

        ''task''
            string
            Current task. Will be filtered via `_normalize_task()`.

        Returns
        -------
        ''iseed''
            string
            String with the individual seed.
        """

        task = self._normalize_task(task)
        if task == 'kpoints':
            pattern = r'(\d+)[\s]+(\d+)[\s]+(\d+).*'
            kpoints = re.match(pattern, var).groups()
            iseed = self.seed + '__' + 'x'.join(map(lambda x:'{0:02d}'.format(int(x)), kpoints)) + '-' + task
        elif task == 'kpointspacing':
            iseed = self.seed + '__{0:5.3f}-per-A-{1:s}'.format(float(var), task)
        elif task == 'cutoff':
            iseed = self.seed + '__{0:04d}-eV-{1:s}'.format(int(var), task)
        elif task == 'vacuum':
            iseed = self.seed + '__{0:02d}-A-{1:s}'.format(int(var), task)
        return iseed


    def get_idir(self, var, task):
        """
        Create an individual directory name for each calculation. It will
        be something like `*base_dir*/*task*/*var*`.

        You should not change the pattern of the directories, as other routines
        rely on it! Feel free to add whatever is needed for other tasks, but
        try to stick with the overall functionality.

        Arguments
        ---------
        ''var''
            float/int/string
            Current value of the variable, ie. the parameter that is varied.

        ''task''
            string
            Current task. Will be filtered via `_normalize_task()`.

        Returns
        -------
        ''idir''
            string
            String with the individual directory name.
        """
        task = self._normalize_task(task)
        if task == 'kpoints':
            pattern = r'(\d+)[\s]+(\d+)[\s]+(\d+).*'
            kpoints = re.match(pattern, var).groups()
            calc_dir = os.path.join(self.base_dir, task,
                                    'x'.join(map(lambda x:'{0:02d}'.format(int(x)), kpoints)) + '-' + task)

        elif task == 'kpointspacing':
            calc_dir = os.path.join(self.base_dir, task,
                                    '{0:5.3f}-per-A-{1:s}'.format(float(var), task))

        elif task == 'cutoff':
            calc_dir = os.path.join(self.base_dir, task,
                                    '{0:04d}-eV-{1:s}'.format(int(var), task))
        elif task == 'vacuum':
            calc_dir = os.path.join(self.base_dir, task,
                                    '{0:02d}-A-{1:s}'.format(int(var), task))
        return calc_dir


    def get_inode(self, task, observable= 'energy', info = ''):
        """
        Function that creates an individual HDF5 node for a set of
        calculations, ie. a task. It will be something like
        `/raw_data/*info*/*seed*/*task*/*observable*`.

        Arguments
        ---------
        ''task''
            string
            Current task. Will be filtered via `_normalize_task()`.

        ''info''
            string, optional (default = '')
            Additional node information. For instance a pseudopotential flag or
            something when sharing a database. Will be inserted after
            `raw_data` in the node.

        Returns
        -------
        ''inode''
            string
            String specifying the individual node.
        """

        inode = '/' + '/'.join(filter(None, ['raw_data', info, self.seed, task, observable]))
        return inode

    def _write_data_txt(self, data, task, observable, verbose = False):
        """
        Routine that writes collected data to a clear-text file.
        With pandas support, this becomes more or less deprecated and will no
        longer be maintained.

        The filename will be *seed*__*observable*_*task*-variation.dat

        Arguments
        ---------
        ''data''
            list
            List of tuples
                (var, value, exists, finished, converged)
            of type
                (str, float, bool, bool, bool).
            Each calculation corresponds to a tuple.

        ''task''
            string
            Current task, specifying of course the format of the output file.
            Will be filtered via `_normalize_task()`.

        ''observable''
            string
            Specifiying, what `value` in the tuples above actually contain.
            Supported this far are `energy` and `fcclatticeconstant`

        ''verbose''
            Boolean, optional (default : False)
            Print the file content to stdout.

        Returns
        -------
        None
        """
        task = self._normalize_task(task)

        obs = self._normalize_observable(observable)

        filename = self.seed + '__' + observable  +  '_' + task + '-variation.dat'
        filename = os.path.join(self.base_dir, filename)

        print('Writing to file: {}'.format(filename))

        with open(filename, 'w') as f:
            f.write('# {}'.format(f.name))
            f.write('\n# file written on: {}'.format(time.strftime('%c')))
            if task == 'cutoff':
                head = '# {0:>28s}'.format('cutoff energy (eV)')
            elif task == 'kpoints':
                head = '# {0:>28s}'.format('kpoint mesh')
            elif task == 'vacuum':
                head = '# {0:>28s}'.format('vacuum distance (A)')

            if obs == 'energy':
                head += ' {0:>30s}'.format('electronic energy (eV)')
            elif obs == 'fcclatticeconstant':
                head += ' {0:>30s}'.format('fcc lattice constant (A)')

            lim = '#' + '-'*len(head)

            header = lim + '\n' + head + '\n' + lim
            if verbose:
                print(header)
            f.write('\n' + header)

            for var, val, existing, finished, converged in data:
                if task == 'cutoff':
                    line = '{0:>30d}'.format(int(var))
                elif task == 'kpoints':
                    line = '{0:>30s}'.format(var)
                elif task == 'vacuum':
                    line = '{0:>30.1f}'.format(float(var))

                if existing and finished and converged:
                    if obs == 'energy':
                            line += ' {0:>30.8f}'.format(float(val))
                    elif obs == 'fcclatticeconstant':
                        line += ' {0:>30.6f}'.format(float(val))
                else:
                    if existing:
                        if not finished:
                            status = 'run crashed'
                        if not converged:
                            status = 'did not converge'
                    else:
                        status = 'no .castep file'
                    line += ' {0:>30s}'.format(status)
                    line = '#' + line[1::]

                if verbose:
                    print(line)

                f.write('\n' + line)

        return None


    def create_dataframe(self, data, observable, task = None, verbose = False):
        """
        Function that creates a pandas data frame. From a given data list.
        It takes care of proper dtypes for the respective columns.

        Arguments
        ---------
        ''data''
            list
            List of tuples
                (var, value, exists, finished, converged)
            of type
                (str, float, bool, bool, bool).
            Each calculation corresponds to a tuple.


        ''observable''
            string
            Specifiying, what `value` in the tuples above actually contain.
            Supported this far are `energy` and `fcclatticeconstant`

        ''task''
            string, optional (default = None)
            Current task. Will be the index name and filtered via
            `_normalize_task()`.

        ''verbose''
            Boolean, optional (default : False)
            Print the data frame content to stdout.

        Returns
        -------
        ''df''
            Pandas DataFrame instance
            Data frame with four columns:
                * observable (float)
                * exists (boolean)
                * finished (boolean)
                * converged (boolean)
            The index name will be `task`.
        """
        if not task == None:
            task = self._normalize_task(task)
        else:
            task = ''

        obs = self._normalize_observable(observable)

        df = create_pandas_dataframe(data = data,
                                     column_names = [obs, 'exists', 'finished', 'converged'],
                                     index_name = task)

        if verbose:
            print(df)

        return df

    def create_array_dataframe(self, data, observable, task = None, verbose = False):
        """
        Function that creates a pandas data frame from a given data list.
        It takes care of proper dtypes for the respective columns.

        .. note ::  in contrast to create_dataframe, this one can handle
           array-like observables like forces.

        Arguments
        ---------
        ''data''
            list
            List of tuples
                (var, value, exists, finished, converged)
            of type
                (str, float array, bool, bool, bool).
            Each calculation corresponds to a tuple.


        ''observable''
            string
            Specifiying, what `value` in the tuples above actually contain.
            Supported this far are `energy` and `fcclatticeconstant`

        ''task''
            string, optional (default = None)
            Current task. Will be the index name and filtered via
            `_normalize_task()`.

        ''verbose''
            Boolean, optional (default : False)
            Print the data frame content to stdout.

        Returns
        -------
        ''df''
            Pandas DataFrame instance
            Data frame with four columns:
                * observables (floats)
                * exists (boolean)
                * finished (boolean)
                * converged (boolean)
            The index name will be `task`.
        """
        if not task == None:
            task = self._normalize_task(task)
        else:
            task = ''

        obs = self._normalize_observable(observable)

        df = create_generic_pandas_dataframe(data = data,
                                             observable_name = observable,
                                             status_names = ['exists', 'finished', 'converged'],
                                             index_name = task)

        if verbose:
            print(df)

        return df

    def write_energy_hdf5(self, task, info = '', dump_to_txt = False, verbose = False):
        """
        Routine that wraps reading and writing to an HDF5 data base.
        The respective node will be determined by `get_inode()`

        Arguments
        ---------
        ''task''
            string
            Task to be analyzed. Will be filtered via `_normalize_task()`.

        ''info''
            string, optional (default = '')
            Additional node information. For instance a pseudopotential flag or
            something when sharing a database. Will be inserted after
            `raw_data` in the node.

        ''dump_to_txt''
            Boolean, optional (default : False)
            Dump the content of the pandas data frame to a clear txt file.
        ''verbose''
            Boolean, optional (default : False)
            Print the data frame content to stdout.

        Returns
        -------
        None
        """
        observable = 'energy'

        task = self._normalize_task(task)
        data = self.read_energy(task)
        df = self.create_dataframe(data = data,
                                   task = task,
                                   verbose = verbose,
                                   observable = observable)
        node = self.get_inode(task, observable=observable, info=info)
        update_hdf_node(df, node, self.store)

        if dump_to_txt:
            filename = self.seed + '__' + observable  +  '_' + task + '-variation.dat'
            filename = os.path.join(self.base_dir, filename)
            print('Dumping to clear text file:\n\t{}'.format(filename))
            with open(filename, 'w') as f:
                f.write('# {}'.format(f.name))
                f.write('\n# file written on: {}'.format(time.strftime('%c')))
                df_str = df.to_string().split('\n')

                # add the hashtags in front of comment lines
                df_str[0] = '#' + df_str[0][1::]
                df_str[1] = '# ' + df_str[1][:-2]

                for line in df_str:
                    f.write('\n' + line)


    def write_forces_hdf5(self, task, info = '', verbose = False):
        """
        Routine that wraps reading and writing to an HDF5 data base.
        The respective node will be determined by `get_inode()`

        Arguments
        ---------
        ''task''
            string
            Task to be analyzed. Will be filtered via `_normalize_task()`.

        ''info''
            string, optional (default = '')
            Additional node information. For instance a pseudopotential flag or
            something when sharing a database. Will be inserted after
            `raw_data` in the node.

        ''verbose''
            Boolean, optional (default : False)
            Print the data frame content to stdout.

        Returns
        -------
        None
        """
        observable = 'forces'

        task = self._normalize_task(task)
        data = self.read_forces(task)
        df = self.create_array_dataframe(data = data,
                                         task = task,
                                         verbose = verbose,
                                         observable = observable)
        node = self.get_inode(task, observable=observable, info=info)
        update_hdf_node(df, node, self.store)

    def write_stress_hdf5(self, task, info = '', verbose = False):
        """
        Routine that wraps reading and writing to an HDF5 data base.
        The respective node will be determined by `get_inode()`

        Arguments
        ---------
        ''task''
            string
            Task to be analyzed. Will be filtered via `_normalize_task()`.

        ''info''
            string, optional (default = '')
            Additional node information. For instance a pseudopotential flag or
            something when sharing a database. Will be inserted after
            `raw_data` in the node.

        ''verbose''
            Boolean, optional (default : False)
            Print the data frame content to stdout.

        Returns
        -------
        None
        """
        observable = 'stress'

        task = self._normalize_task(task)
        data = self.read_stress(task)
        df = self.create_array_dataframe(data = data,
                                         task = task,
                                         verbose = verbose,
                                         observable = observable)
        node = self.get_inode(task, observable=observable, info=info)
        update_hdf_node(df, node, self.store)

    def read_energy(self, task):
        """
        This is a stub. Your derived class MUST provide this functionality if
        you care about energies.

        By passing the task, your routine must be able to find the
        corresponding calculations.
        """
        raise NotImplementedError

    def read_forces(self, task):
        """
        This is a stub. Your derived class MUST provide this functionality if
        you care about energies.

        By passing the task, your routine must be able to find the
        corresponding calculations.
        """
        raise NotImplementedError

    def read_stress(self, task):
        """
        This is a stub. Your derived class MUST provide this functionality if
        you care about energies.

        By passing the task, your routine must be able to find the
        corresponding calculations.
        """
        raise NotImplementedError

    def write_energy_txt(self, task):
        """
        Routine that wraps reading and writing to clear text.

        Arguments
        ---------
        ''task''
            string
            Task to be analyzed. Will be filtered via `_normalize_task()`.

        Returns
        -------
        None
        """

        task = self._normalize_task(task)
        data = self.read_energy(task)
        self._write_data_txt(data = data,
                         task = task,
                         observable = 'energy')


    def __del__(self):
        try:
            self.store.close()
        except AttributeError or NameError:
            pass
# just a convenience wrapper (staticmethods would break to much workflow)
__conv = Convergence(None, None, None)
def normalize_task(task, supset = True):
    return __conv._normalize_task(task, supset = supset)

def normalize_obs(obs):
    return __conv._normalize_obs(obs)


