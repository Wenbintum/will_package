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

from __future__ import print_function

import os
import re
import numpy as np
import time

from rtools.misc import get_close_matches
from rtools.misc import format_timing
from rtools.filesys import mkdir

from rtools.helpers.castephelpers import read_energy
from rtools.mapping.pes import PES

from rtools.submitagents.arthur.castep import submit as submit_arthur
from rtools.submitagents.workstation.castep import submit as submit_workstation
from rtools.submitagents.arthur.casteppostproc import submit as submit_postproc_arthur

welcome = True

class CastepPES(PES):
    """
    Mapping functionality for a potential energy surface (PES) using the CASTEP
    DFT code.

    Initialization
    --------------
    ''seed''
        string
        Common seed for all caluclations. Usualy, this will be your system
        identifyer.

    ''get_atoms''
        function
        Function which returns an ASE atoms object that returns the geometry of
        the system at the coordinates specified by `points`. This function must
        work on whichever input you later specify via the `points` argument and
        return a valid atoms object.

    ''get_calc''
        function
        Function that returns the respective ASE calculator. As for
        `get_atoms`, this function must not require any additional arguments.

    ''hdf5file''
        string, optional (default = None)
        Path to a HDF5 database in which the results may be stored. Note that
        HDF5 support requires PyTables and Pandas!

    ''base_dir''
        string, optional (default = '.')
        Base directory under which all further (sub)folder for all calculations
        are created. Defaults to the current working directory.

    ''export_partition''
        string, optional ({"hdd_export", "export", *None*})
        If you want to also copy files to an export partition directly from the
        nodes (e.g. large checkfiles), specify the respective partition here.
        The target directory will be
        /net/<host>/<export_partition>/<user>/<"job_dir minus /data/<user>">.

    ''export_host''
        string, optinal (default=None)
        The host in the string above. Defaults to the current host.

    ''point_names''
        string, optional (default = None)
        Point names, will be used to make filenames and dirnames a bit more
        self-contained.

    ''float_fmt''
        string, optional (default: '+.3f')
        Format specifyer for all situations in which it is necessary to convert
        float to strings (ie. filenames, directories,...)

    ---
    Simon P. Rittmeyer, 2015
    simon.rittmeyer(at)tum.de
    """

    # slahes, dots and hyphens will be gone upon normalization, hence we do not
    # need to consider them here
    _export_alias = {'export' : ['export', 'ssd'],
                     'hdd_export' : ['hdd_export', 'hdd']}


    _all_export_alias = []
    for alias in _export_alias.values():
        _all_export_alias += alias

    _logo = r"""
--------------------------------------------------------------------------------
                 ____          _             ____  _____ ____
                / ___|__ _ ___| |_ ___ _ __ |  _ \| ____/ ___|
               | |   / _` / __| __/ _ \ '_ \| |_) |  _| \___ \
               | |__| (_| \__ \ ||  __/ |_) |  __/| |___ ___) |
                \____\__,_|___/\__\___| .__/|_|   |_____|____/
                                      |_|

                       Simon P. Rittmeyer, TUM, 2015-16
                          simon.rittmeyer(at)tum.de
--------------------------------------------------------------------------------
"""[1:-1]


    def __init__(self, *args, **kwargs):
        # only show once...
        global welcome
        if welcome:
            print(self._logo)
            welcome = False

        # get the new keyword
        export_partition = kwargs.pop('export_partition', None)
        self._export_host = kwargs.pop('export_host', os.uname()[1])

        # I do not see why we should have this one a parameter...
        self._user = os.getlogin()

        # initialize the parent
        PES.__init__(self, *args, **kwargs)

        # check for the export dir
        if export_partition != None:
            # check if we have write permissions before the submit agent does
            # it several times
            export_partition = self._normalize_export_partition(export_partition)
            export_str = os.path.join('/net/{}/{}/{}'.format(self._export_host, export_partition, self._user))
            if not os.access(export_str, os.W_OK):
                raise OSError('No write access to `export_partition`:\n{}'.format(export_str))
            else:
                self.export_partition = export_partition
        else:
            self.export_partition = export_partition


    def _normalize_export_partition(self, export_partition):
        """
        Normalize an export_partition. Again, this is for comparison reason.
        The routine compares against the class-internal export_partition alias
        lists.

        Arguments
        ---------
        ''export_partition''
            string
            String specifying the export partition.

        Returns
        -------
        Normalized string specifying the export partition.

        Raises
        ------
        `NotImplementedError` if 'export_partition' is unknown.
        """

        # filter for comparison
        export_partition = re.sub(r'[\s\-\./]*','', export_partition)

        found = False
        for iexp, alias in self._export_alias.items():
            if export_partition in alias:
                found = True
                norm_export_partition = iexp
                break
        if found:
            return norm_export_partition
        else:
            err_msg = "Unknown export_partition: ``{}''".format(export_partition)
            print(err_msg)
            print(get_close_matches(export_partition, self._all_export_alias))
            raise NotImplementedError(err_msg)


    def get_idir_export(self, point):
        """
        Create an individual directory name at the export partition for each calculation based on
        the member variable 'export_base_dir' and the point to be calculated.

        Parameters
        ----------
        ''point''
            float, int, list/np array thereof
            The point specifying the particular variables that are mapped.
            Type conversion and string normalization will be taken care of.

        Returns
        -------
        string consisting of <base_dir>/{x__}* where <x> are the values in
        point.
        """
        if self.export_partition == None:
            return None
        else:
            idir = self.get_idir(point)

            # who are we and which is our host
            idir_export = idir.replace('/data/{}/'.format(self._user),
                                       '/net/{}/{}/{}/'.format(self._export_host, self.export_partition, self._user))
            return idir_export


    def _read_data(self, base_dir = None, process_resultfolder = None):
        """
        Function that walks a given directory and parses the respective
        output files.

        Parameters
        ----------
        ''base_dir''
            string
            Path to the base directory. Defaults to the <self.base_dir> if None
            is given.

        ''process_resultfolder''
            Function, optional (default = None)
            Function to be called with the path to a result directory in case
            you want some more customized interpretation of your results.

            This function has to necessarily return:

            * point_dict : A dictionary containg any information (besides the
                           energy which is parsed anyway outside of this routine)
                           that may be deduced from any file in the result
                           folder. Note that you have to explicitely include the
                           point informationon, this is no longer done
                           automatically.

            One possible application would either be that you need the float
            values of the points more accurately than they are represented on
            the string level, or that you also want to extract information from
            files other than the *.castep file.

        Returns
        -------
        Dictionary holding all information on the data. It is organized as
        follows:
            for every point:
            <point_str> : dictionary
                          Dictionary containg the information for the
                          individual points. In this particular case it will
                          be
                          ''*{point_names}'' : The respective point coordinates
                                               coordinates. as floats
                          ''energy'          : Float, energy for this particular
                                               configuration.
                          ''existing''       : Boolean, flag indicating whether
                                               the job has been submitted (if a
                                               *.castep file exists in the
                                               results directory).
                          ''finished''       : Boolean, flag indicating whether a
                                               calculation is finished properly
                                               (has a regular end)
                          ''converged''      : Boolean, flag indicating whether
                                               the calculation is converged with
                                               respect to both, SCF and geometry
                                               relaxation (if existing).

                          PLUS any additional elements from 'add_dict' if you
                          use 'process_resultfolder()'
        """
        if base_dir is None:
            base_dir = self.base_dir

        data = []

        # it is ensured that no user settings can change that!
        result_dir = 'results'

        for path, dirs, files in os.walk(base_dir):
            if result_dir in dirs:
                if process_resultfolder is None:
                    # assume the prefix in get_idir --> hard coded in parent
                    # only split at the first occurence, rest is done with
                    # "_string_to_point()"
                    point_str = os.path.basename(path).split('__',1)[-1]

                    # convert to array of floats
                    point = self._string_to_point(point_str)

                    # get the point dictionary
                    point_dict = self._point_to_dict(point)

                else:
                    result_path = os.path.abspath(os.path.join(path, result_dir))
                    point_dict = process_resultfolder(result_path)

                E = np.nan
                existing = False
                finished = False
                converged = False

                result_path = os.path.join(path, result_dir)
                for f in os.listdir(result_path):
                    f = os.path.join(result_path, f)
                    if f.endswith('.castep'):
                        existing = True
                        E, finished, converged = read_energy(f, get_status = True)


                # the info dict for the calculation. Make sure that types are
                # properly assigned
                calc_infos = {'energy'    : float(E),
                              'existing'  : bool(existing),
                              'finished'  : bool(finished),
                              'converged' : bool(converged)}

                calc_infos.update(point_dict)

                data.append(calc_infos)

        return data



    def _calculate(self,
                   points,
                   pspot_suffix = 'OTF',
                   submit_func=None,
                   force_resubmit_empty=False,
                   force_resubmit_all=False,
                   verbose=False,
                   try_reuse_previous=False,
                   **kwargs):
        """
        Function that wraps all necessary tasks to run several calculations.

        This function is generic in the sense, that the actual submit function
        may be changed.

        Arguments
        ---------
        ''submit_func'' : rtools submit agent function
            Function that does all the PBS related communication. See the
            submitagents provided with rtools for more details.

        ''points''
            list
            List of values that the varied parameter should correspond to.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''force_resubmit_empty''
            boolean, optional (default = False)
            Resubmit if the results folder is empty. Be careful, your job may
            still be running.

        ''force_resubmit_all''
            boolean, optional (default = False)
            Resubmit regardless of whether there are any existing files or
            folders.

        ''verbose''
            boolean, optional (default=False)
            Print "Job X / Y" before submitting/calculating.

        ''try_reuse_previous''
            boolean, optional (default=False)
            Try to fetch the check file of the previous run and use it to speed
            up the next simulation thanks to density extrapolation. Note that
            this option should *never* be used togehter with a cluster and thus
            distributed computations.

        ''**kwargs''
            are directly passed to the `submit_func()` function.

        Returns
        -------
        None
        """
        njobs = len(points)
        nsubmitted = 0
        nskipped = 0
        nprocessed = 0

        print(self._lim)
        print('Requested {} jobs in total'.format(njobs))
        print(self._lim)

        _prev_point=None

        for point in points:
            if verbose:
                info = '| Job {{:{0}d}} / {{:{0}d}} |'.format(len(str(njobs))).format(nprocessed+1, njobs)
                lim = '+' + '-'*(len(info)-2) + '+'
                print(lim)
                print(info)
                print(lim)

            # get the indivial variables
            iseed = self.get_iseed(point)
            idir = self.get_idir(point)
            idir_export = self.get_idir_export(point)

            # create folder if necessary
            if mkdir(idir, backup_existing = False,
                           purge_existing = False,
                           verbose = False):
                pass

            # "results" is hard coded, see below

            elif os.path.exists(os.path.join(idir, 'results')) and os.listdir(os.path.join(idir, 'results')) and force_resubmit_empty:
                print('Resubmitting job "{}" due to empty result folder. Existing files are not backed up.'.format(iseed))
                pass

            elif not force_resubmit_all:
                # folder already exists...
                print('Skipping job "{}" due to existing files'.format(iseed))
                nskipped += 1
                nprocessed += 1
                _prev_point=point
                continue

            # get the calculator and set label and dir
            calc = self.get_calc()
            calc._label = iseed
            calc._directory = idir

            # get the atoms
            atoms = self.get_atoms(point)

            # set the calculator
            atoms.set_calculator(calc)

            # we need it hard coded here...
            atoms.calc.set_pspot(pspot = pspot_suffix)

            if nprocessed > 0 and try_reuse_previous:
                _prev_iseed = self.get_iseed(_prev_point)
                _prev_idir = self.get_idir(_prev_point)
                _prev_idir_export= self.get_idir_export(_prev_point)

                # try to fetch a check file (either on /data or on the /export
                # partition; we do not know as this is determined by the submit
                # function)
                locations = [
                             os.path.join(_prev_idir, 'results', _prev_iseed + '.check'),
                             os.path.join(_prev_idir_export, _prev_iseed + '.check'),
                            ]

                _prev_icheck = None
                for f in locations:
                    if os.path.exists(f):
                        _prev_icheck = f
                        break

                if _prev_icheck:
                    if verbose:
                        print('Info: Fetched previous checkfile -- will be reused'.format(_prev_icheck))

                    # Symlink the check file (makes life easier...)
                    os.symlink(_prev_icheck,
                                os.path.join(idir, _prev_iseed + '.check'))

                    atoms.calc.param.reuse = _prev_iseed + '.check'
                else:
                    if verbose:
                        print('Info: Unable to fetch previous checkfile -- start from scratch')

            # prepare input files and submit
            atoms.calc.prepare_input_files()

            # make sure that user does not override the result default
            result_dir = kwargs.pop('result_dir', None)
            if result_dir:
                print('Argument "result_dir" was set to "{}"'.format(result_dir))
                print('Will be changed to "<job_dir>/results" to maintain compatibility with reading routines')


            submit_func(seed = iseed,
                        job_dir = idir,
                        result_dir = 'results',
                        export_dir = idir_export,
                        **kwargs)


            nprocessed += 1
            nsubmitted += 1

            # this is for the reuse feature
            _prev_point = point
        print(self._lim)
        print('Submitted : {0:>4d} / {1:d} jobs'.format(nsubmitted, njobs))
        print('Skipped   : {0:>4d} / {1:d} jobs'.format(nskipped, njobs))
        print(self._lim)



    def calculate(self,
                  points,
                  pspot_suffix = 'OTF',
                  force_submit=False,
                  **kwargs):
        """
        Function that wraps all necessary tasks to run several calculations.

        Arguments
        ---------
        ''points''
            list
            List of values that the varied parameter should correspond to.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''force_submit''
            boolean, optional (default = False)
            Resubmit regardless of whether there are any existing files or
            folders.

        ''**kwargs''
            are directly passed to the `submit()` function from
            rtools.submitagents.arthur.castep.

        Returns
        -------
        None
        """

        self._calculate(points=points,
                        submit_func=submit_arthur,
                        pspot_suffix=pspot_suffix,
                        # do *NOT* use on a cluster
                        try_reuse_previous=False,
                        **kwargs)

    def calculate_workstation(self,
                              points,
                              pspot_suffix = 'OTF',
                              force_submit=False,
                              try_reuse_previous=True,
                               **kwargs):
        """
        Function that wraps all necessary tasks to run several calculations on
        a local workstation.

        Arguments
        ---------
        ''points''
            list
            List of values that the varied parameter should correspond to.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''force_submit''
            boolean, optional (default = False)
            Resubmit regardless of whether there are any existing files or
            folders.

        ''try_reuse_previous''
            boolean, optional (default=False)
            Try to fetch the check file of the previous run and use it to speed
            up the next simulation thanks to density extrapolation. Note that
            this option should *never* be used togehter with a cluster and thus
            distributed computations.

        ''**kwargs''
            are directly passed to the `submit()` function from
            rtools.submitagents.workstation.castep.

        Returns
        -------
        None
        """
        self._calculate(points=points,
                        submit_func=submit_workstation,
                        pspot_suffix=pspot_suffix,
                        verbose=True,
                        try_reuse_previous=try_reuse_previous,
                        **kwargs)


class CastepPostProcPES(CastepPES):
    """
    This class is analogous to the CastepPES class, but in addition to running
    an SCF calculation, also some postprocessing is available, as e.g. required
    in LDFA friction calculations.
    """

    def calculate(self,
                   points,
                   pspot_suffix = 'OTF',
                   **kwargs):
        """
        Function that wraps all necessary tasks to run several calculations.

        Arguments
        ---------
        ''points''
            list
            List of values that the varied parameter should correspond to.

        ''pspot_suffix''
            string, optional (default = 'OTF')
            Usually CASTEP USPP are named like <Elem>_<pspot_suffix>.usp. This
            suffix ensures to correctly create the cell file.

        ''**kwargs''
            are directly passed to the `submit()` function from
            rtools.submitagents.arthur.casteppostproc.

        Returns
        -------
        None
        """
        self._calculate(points=points,
                        submit_func=submit_postproc_arthur,
                        pspot_suffix=pspot_suffix,
                        **kwargs)

