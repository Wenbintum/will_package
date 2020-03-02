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

import os
import glob
import shutil
import time

from ase.io.castep import read_seed

from rtools.filesys import mkdir
from rtools.mapping import Mapping


class CastepCont(Mapping):
    """
    Base class for mapping of castep continuation tasks. Intented to run the
    continuation calculations on a local workstation to avoid uneccesary
    network traffic (large check files).

    Initialization
    --------------
    ''seed''
        string
        Common seed for all caluclations. Usualy, this will be your system
        identifyer.

    ''DFT_base_dir''
        string, optional (default = None)
        Path to the base directory where all calculations incl. checkfiles are
        stored in subfolders.

    ''pp_dir''
        string (optional, default = None)
        Path to the directory holding all pseudopotentials that have been used
        for the SCF calculation. This is absolutely crucial, since a
        continuation calculation requires exactly the same pseudopotentials. If
        None is given, all you can do is to hope that the oaths are properly
        recovered from the files of the SCF run *or* set the environment
        variable $PSPOT_DIR which is read by CASTEP by default.

    ''hdf5file''
        string, optional (default = None)
        Path to a HDF5 database in which the results may be stored. Note that
        HDF5 support requires PyTables and Pandas!

    ''base_dir''
        string, optional (default = '.')
        Base directory under which all further (sub)folder for all calculations
        are created. Defaults to the current working directory.

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


    def __init__(self, *args, **kwargs):

        # raises key error if not given... Ok!
        self.DFT_base_dir = kwargs.pop('DFT_base_dir', None)
        self.pp_dir = kwargs.pop('pp_dir', None)

        # initialize the parent
        Mapping.__init__(self, *args, **kwargs)

    def _check_requirements(self, requirements, working_dir = '.', verbose = False):
        """
        Function that checks if all requires files are located in 'working_dir'.

        Parameters
        ----------
        ''requirements''
            string/list of strings Filenames
            that are required in 'working_dir'.  Globbing via wildcards in
            supported.

        ''working_dir''
            string, optional (default ".")
            Path to the working directory.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        <True> if requirements are met, <False> if not. This
        routine does not raise an IOError on its own, but you can catch the
        output value and process it.
        """
        if verbose:
            print('\tChecking for input completeness')

        if isinstance(requirements, str):
            requirements = [requirements]

        if not os.path.exists(working_dir):
            print('!FATAL! <working_dir> does not exist')
            return False

        # collect the missing files
        missing = []

        for r in requirements:
            l = glob.glob(os.path.join(working_dir, r))
            if not l:
                missing.append(r)

        if not missing:
            return True

        else:
            msg = '!FATAL! Requirements are not met:'
            for m in missing:
                msg += '\n\t"{}" is missing'.format(m)
            print(msg)
            return False


    def _link_binary(self, binary, target_dir = './', verbose = False):
        """
        Function that symlinks a list of binaries to a 'target_dir' *Note that
        the the name ofthe binary will be the name of the symlink!*

        Parameters
        ----------
        ''binaries''
            string/list of strings
            Either a list of strings or a single string specifying the complete
            abspath to the binary.

        ''target_dir''
            string, optional (default = './')
            Directory where to place the symlinks.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        The binary name such that it can be directly executed. This means, that
        if <binary> was linked, there is a <target_dir> prefix.
        If <binary> does not contain a dirname, it is assumed that it can be
        called from $PATH.
        """


        if os.path.dirname(binary):

            # get the name of the binary
            binary_name = os.path.basename(binary)

            # path to the symlink
            binary_link = os.path.join(target_dir, binary_name)

            if os.path.exists(binary_link):
                os.unlink(binary_link)

            if verbose:
                print('Linking binary:')
                print('\t{} --> {}'.format(binary, binary_link))

            os.symlink(binary, binary_link)
            return binary_link
        else:
            return binary


    def _get_DFT_infos(self, DFT_idir, DFT_iseed = None):
        """
        Function that grabs *.cell, *.param and *.check file names, as well as
        the seed from a CASTEP calculation "DFT_idir".

        Parameters
        ----------
        ''DFT_idir''
            string
            Path to the CASTEP output.

        ''DFT_iseed''
            string, optional (default = None)
            CASTEP iseed. If not specified, the routine will glob using a
            wildcard. In this case, you should make sure that there is actually
            only one .cell, .param, and .check file in 'DFT_idir'.

        Returns
        -------
        Dictionary with the following keys:
            ''param''
                string
                DFT_idir/*.param

            ''cell''
                string
                ijob_dir/*.cell

            ''castep''
                string
                ijob_dir/*.cell

            ''check''
                string
                ijob_dir/*.check*

            ''iseed''
                string
                iseed

            ''path''
                string
                Path to the DFT directory

        Raises
        ------
        "IOError" if any of the required files is not found.
        """

        if DFT_iseed == None:
            DFT_iseed = '*'

        try:
            DFT = {'param' : glob.glob(os.path.join(DFT_idir, '{}.param'.format(DFT_iseed)))[-1],
                   'cell'  : glob.glob(os.path.join(DFT_idir, '{}.cell'.format(DFT_iseed)))[-1],
                   'castep': glob.glob(os.path.join(DFT_idir, '{}.castep'.format(DFT_iseed)))[-1],
                   'check' : glob.glob(os.path.join(DFT_idir, '{}.check*'.format(DFT_iseed)))[-1]
                   }

            if DFT_iseed == '*':
                DFT_iseed = os.path.basename(DFT['param']).rstrip('.param')

            DFT['iseed'] = DFT_iseed
            DFT['path'] = os.path.abspath(os.path.dirname(DFT['param']))

            return DFT

        except IndexError:
            # if we do not find one or more of the required SCF files
            raise IOError('!FATAL! Incomplete set of CASTEP output files.')


    def _prepare_castep_files(self, DFT_info, iseed, ijob_dir, verbose = False):
        """
        Function that prepares a <iseed>.cell and <iseed>.param file for the
        continuation calculation. In addition, a symlink <iseed>.check will be
        created.

        The <iseed>.param file will be appended a "continuation : <checkfile>"
        flag and possible "reuse" flags are removed.

        This routine heavily relies on the ase.calculator/io.castep interface!

        Parameters
        ----------
        ''DFT_info''
            dictionary
            Dictionary as created by "_get_DFT_infos()". Must contain the keys
            "path", "iseed" and "check"

        ''iseed''
            string
            Seed for the continuation calculation.

        ''ijob_dir''
            string
            Path to the working directory.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        None
        """
        if verbose:
            print('\tPreparing new  *.param and *cell file')

        # store info on SCF in file
        with open(os.path.join(ijob_dir,'SCF.info'), 'w') as f:
            f.write('File written on {}'.format(time.strftime('%c')))
            f.write('\nInformation on underlying SCF calculation:')
            for key, value in DFT_info.items():
                f.write('\n\t{0:<10s} : {1}'.format(key, value))

        # Symlink the check file (makes life easier...)
        os.symlink(DFT_info['check'],
                   os.path.join(ijob_dir, iseed + '.check'))

        atoms = read_seed(os.path.join(DFT_info['path'], DFT_info['iseed']))

        # add the pp dir
        if self.pp_dir != None:
            atoms.calc._castep_pp_path = self.pp_dir

        # write the new param file. Remove the reuse flag (if it was set) and
        # append continuation
        atoms.calc.param.reuse.value = None
        atoms.calc.param.continuation = "{}.check".format(iseed)

        # set label and directory
        atoms.calc._label = iseed
        atoms.calc._directory = ijob_dir
        atoms.calc._check_checkfile = False
        atoms.calc._copy_pspots= False

        atoms.calc.prepare_input_files()

        return None


    def prepare_continuation_calculation(self, DFT_idir, ijob_dir,
                                               iseed = None,
                                               DFT_iseed = None,
                                               backup_existing = True,
                                               verbose = False):

        """
        Function that prepares a CASTEP continuation calculation.  The
        function creates a <iseed>.cell and <iseed>.param file in <ijob_dir> from
        a given SCF calculation in <DFT_idir> using the ase CASTEP calculator.
        The latter will be appended a "continuation : <checkfile>" and possibly
        existing "reuse" statements are remove due to conflicting options.

        Parameters
        ----------
        ''DFTdir''
            string
            Path to the output of the CASTEP SCF calculation (*including in
            particular the .check file*), on which the continuation calcultion
            shall be based on.

        ''ijob_dir''
            string
            Path where to prepare the continuation calculation.

        ''iseed''
            string, optional (default = None)
            Seed for the new files in 'ijob_dir'. If None, the iseed from the DFT
            calculations will be re-used.

        ''DFT_iseed''
            string (default = None)
            CASTEP iseed. If not specified, the routine will glob using a
            wildcard.  In this case, you should make sure that there is
            actually only one .cell, .param, and .check file in 'DFT_idir'.

        ''backup_existing''
            boolean, optional (default = True)
            Flag that is directly passed to the "mkdir()" routine of rtools.
            Note that "purge_existing" is always <True>. *This means that your
            files will be irrevesibly gone if you do not set
            "backup_existing = True".

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        None
        """

        # make sure we have absolute path names
        ijob_dir = os.path.abspath(ijob_dir)
        DFT_idir = os.path.abspath(DFT_idir)

        # holds all DFT names
        DFT_info = self._get_DFT_infos(DFT_idir = DFT_idir, DFT_iseed = DFT_iseed)

        # use the same iseed as the DFT calculation if none is given
        if iseed == None:
            iseed = DFT_info['iseed']

        if verbose:
            print('Preparing calculation for seed: {}'.format(iseed))
            print('\tSource     : {}'.format(DFT_idir))
            print('\tJob folder : {}'.format(ijob_dir))

        # create the folder if not already there
        mkdir(ijob_dir, backup_existing = backup_existing, purge_existing = True,
                       verbose = verbose)

        self._prepare_castep_files(DFT_info, iseed = iseed,
                                   ijob_dir = ijob_dir,
                                   verbose = verbose)

        return None


    def _gather_jobs(self, DFT_base_dir, verbose = False):
        """
        Function that gathers jobs from a previous PES mapping, ie. SCF
        calculations.

        *Note that this function heavily relies on the naming conventions from
        the mapping.pes.castep.Castep instance.* It will most probably not work
        if you fudged around with the naming schemes on your own.

        Parameters
        ----------
        ''DFT_base_dir''
            string
            Path to the base dir of the corresponding PES mapping instance.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        Dictionary with keys <point_str>, ie. the string representation of the
        DFT points. Each key corresponds to a further dictionary with keys
            * ''point''
                  numpy array
                  The actual point as recreated from the string via
                  "_point_to_string()"

            * ''DFT_idir''
                  string
                  The complete path to DFT calculation files. Can be directly
                  passed to "prepare_continuation_calculation()".
        """
        jobs = {}
        for path, dirs, files in os.walk(DFT_base_dir):
            for f in files:
                if f.endswith('.castep'):
                    # no we are in the correct path
                    # split once only - note that we rely on the naming
                    # convention from the PES mapper class
                    point_str = os.path.basename(path).split('__',1)[-1]
                    point     = self._string_to_point(point_str)
                    DFT_idir   = os.path.abspath(path)
                    jobs[point_str] = {'point' : point, 'DFT_idir' : DFT_idir}
        if verbose:
            print('\tGathered a total of {} jobs'.format(len(jobs.keys())))

        return jobs

