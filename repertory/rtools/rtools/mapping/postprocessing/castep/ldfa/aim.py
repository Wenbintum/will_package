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

import re
import os
import shutil
import time

from ase.io.castep import read_cell
from ase.io.castep import read_param

from rtools.filesys import shell_stdouterr
from rtools.filesys import mkdir
from rtools.filesys import gzip_file
from rtools.misc import format_timing
from rtools.cube import InterpolatedCube
from rtools.helpers.pandashelpers import update_hdf_node
from rtools.mapping.postprocessing.castep.ldfa import LDFA

class AIM(LDFA):
    """
    Class to map LDFA-AIM friction coefficients based on existing SCF
    calculations.

    Initialization
    --------------
    ''seed''
        string
        Common seed for all calculations. Usualy, this will be your system
        identifyer.

    ''DFT_base_dir''
        string, optional (default = None)
        Path to the base directory where all calculations incl. checkfiles are
        stored in subfolders.

    ''castep2cube_bin''
        string, optional (default = None)
        Path to the castep2cube binary as shipped with your CASTEP
        distribution. If nothing is passed, it will be assumed that the binary
        is available via "castep2cube" from $PATH.

    ''castep_hirshfeld_bin''
        string, optional (default = None)
        Path to the castep_hirshfeld binary as written by Joerg Meyer and Simon
        Rittmeyer (not shipped with CASTEP - but the essential parts written by
        JM are available in the CASTEP source code as Hirshfeld module). If
        nothing is passed, it will be assumed that the binary is available via
        "castep_hirshfeld" from $PATH.

    ''cube_subtract_bin''
        string, optional (default = None)
        Path to the cube_subtract binary as shipped with your CASTEP
        distribution as part of cube_tools. If nothing is passed, it will be
        assumed that the binary is available via "cube_subtract" from $PATH.

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

    _logo = r"""
--------------------------------------------------------------------------------
                  ____          _               _    ___ __  __
                 / ___|__ _ ___| |_ ___ _ __   / \  |_ _|  \/  |
                | |   / _` / __| __/ _ \ '_ \ / _ \  | || |\/| |
                | |__| (_| \__ \ ||  __/ |_) / ___ \ | || |  | |
                 \____\__,_|___/\__\___| .__/_/   \_\___|_|  |_|
                                       |_|

                        Simon P. Rittmeyer, TUM, 2015
                          simon.rittmeyer(at)tum.de
--------------------------------------------------------------------------------
"""[1:-1]


    def __init__(self, *args, **kwargs):
        print(self._logo)
        # get the new keywords
        self.castep_hirshfeld_bin = self._get_binary(binary = kwargs.pop('castep_hirshfeld_bin', ''),
                                                     name = 'castep_hirshfeld',
                                                     default = 'castep_hirshfeld')

        self.cube_subtract_bin = self._get_binary(binary = kwargs.pop('cube_subtract_bin', ''),
                                                  name = 'cube_subtract',
                                                  default = 'cube_subtract')

        self._prefix = 'LDFA_AIM'
        # initialize the parent
        LDFA.__init__(self, *args, **kwargs)


    def calc_aim_cubes(self, iseed,
                             elements,
                             ijob_dir,
                             result_dir = 'cube_files',
                             gzip = True,
                             backup_existing = True,
                             purge_existing = True,
                             version = 1,
                             verbose = False):
        """
        Function that calculations a cube file from a CASTEP run. Note that
        this routine does not prepare any input files, you should use
        "prepare_continuation_calculation()" for this purpose!

        Parameters
        ----------
        ''iseed''
            string
            Common seed for the cube calculation.

        ''elements''
            list of strings
            Elements for which to calculate the Hirshfeld decomposition.

        ''ijob_dir''
            string
            Working directory, i.e. the directory where the input has been
            prepared. Use the "prepare_continuation_calculation()" method for preparation!

        ''result_dir''
            string (default = 'cube_files')
            Directory into which the output files are moved. It will always be
            a subdirectory of 'ijob_dir' in the sense of
            <ijob_dir>/<result_dir>. So do not pass absolute paths here.

        ''gzip''
            boolean, optional (default = True)
            Determines whether the output files are zipped or not.

        ''backup_existing''
            boolean, optional (default = True)
            Flag that is directly passed to the "mkdir()" routine of rtools.
            See documentation there.

        ''purge_existing''
            boolean, optional (default = True)
            Flag that is directly passed to the "mkdir()" routine of rtools.
            See documentation there.

        ''version''
            integer, optional (default = 1)
            Which version of the castep_Hirshfeld binary is used. The original
            JM binary is version 1, the extended binary by SPR is version 2.
            Version 2 does not require an additional castep2cube run and avoids
            output of some unnecessary files.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        None
        """
        origin_dir  = os.getcwd()
        ijob_dir = os.path.abspath(ijob_dir)
        result_dir  = os.path.join(ijob_dir, result_dir)

        # check if all files are there...
        requirements = ['{}.{}'.format(iseed, suffix) for suffix in ('cell','param')]
        self._check_requirements(requirements, ijob_dir)

        # make sure there is a proper result directory
        mkdir(result_dir, backup_existing = backup_existing,
                          purge_existing = purge_existing,
                          verbose = verbose)

        if verbose:
            print('Running LDFA-AIM calculation for seed: {}'.format(iseed))
            print('\tJob folder    : {}'.format(ijob_dir))
            print('\tResult folder : {}'.format(result_dir))

        if version < 2:
            # Do the cube calculation first
            self.calc_cube(iseed = iseed,
                           ijob_dir = ijob_dir,
                           # result dir stuff will be done by this routine
                           result_dir = '',
                           # we will do the gzipping afterwards
                           gzip = False,
                           # we already initialized
                           init = False,
                           verbose = verbose)
        # change to working directory
        os.chdir(ijob_dir)

        # link the binary only if it is not in path...
        castep_hirshfeld_bin = self._link_binary(self.castep_hirshfeld_bin,
                                                 verbose = verbose)

        # run the Hirshfeld decomposition
        castep_hirshfeld_str = r'{0} {1}'.format(castep_hirshfeld_bin, iseed)

        if verbose:
            print('Running Hirshfeld decomposition')
            print('\t' + castep_hirshfeld_str)

        shell_stdouterr(castep_hirshfeld_str)

        # find unneeded elements automatically
        atoms = read_cell(iseed + '.cell')
        delete_elements = set([a.symbol for a in atoms if a.symbol not in elements])

        delete_pattern = '{}'.format('|'.join(list(delete_elements)))

        # deleting unnecessary output
        if verbose:
            print('Removing unnecessary output files:')
        for f in os.listdir('.'):
            pattern = r'Hirshfeld_rho_ba.*' + format(delete_pattern)
            if re.search(pattern, f) or re.search(r'Hirshfeld_w-', f) or re.search(r'\.err', f):
                if verbose:
                    print('\t{}'.format(f))
                os.remove(f)

        # renaming remaining output files
        if verbose:
            print('Renaming remaining output files (just for convenience):')
        for e in elements:
            for f in os.listdir('.'):
                # we want to get rid of the 'ns' flag
                pattern = r'(.*)(-Hirshfeld_rho_ba)-ns_[0-9]+(.*)'
                search_obj = re.search(pattern, f)
                if search_obj:
                    old = search_obj.group()
                    new = ''.join(search_obj.groups())
                    if verbose:
                        print('\t{} --> {}'.format(old, new))
                    os.rename(old, new)

        # get the difference density cube file
        cube_subtract_bin = self._link_binary(self.cube_subtract_bin,
                                              verbose = verbose)

        if verbose:
            print('Calculating density differences')

        r = re.compile(r'.*-chargeden\.cube')
        interacting_density = filter(r.match, os.listdir('.'))[-1]

        r = re.compile(r'.*Hirshfeld_rho_ba.*')
        hirshfeld_densities = filter(r.match, os.listdir('.'))

        for hirsh in hirshfeld_densities:
            cube_subtract_str = r'{0} {1} {2}'.format(cube_subtract_bin,
                                                      interacting_density,
                                                      hirsh)
            if verbose:
                print('\t' + cube_subtract_str)

            shell_stdouterr(cube_subtract_str)

            # get the species identifyer
            pattern = r'.*-Hirshfeld_rho_ba-(.*)'
            ispec = re.match(pattern, hirsh).groups()[-1]

            # rename the resulting file
            os.rename(interacting_density + '-minus-' + hirsh,
                      iseed + '-{}-'.format(self._prefix) + ispec)

        if gzip:
            if verbose:
                print('Gzipping results')
            for f in os.listdir('.'):
                if re.search(r'\.cube.*', f):
                    gzip_file(f)
                    if verbose:
                        print('\t' + f)

        if not os.path.samefile(ijob_dir, result_dir):
            if verbose:
                print('Moving results to resultfolder')
            for f in os.listdir('.'):
                if re.search(r'\.cube.*', f):
                    shutil.move(f, result_dir)

        # change back to originfolder
        os.chdir(origin_dir)


    def calculate(self, elements, jobs = None, **kwargs):
        """
        Function that wraps all necessary tasks for a LDFA-AIM calculation.

        Arguments
        ---------
        ''elements''
            list of strings
            Elements for which to calculate the LDFA-AIM decomposition.

        ''jobs''
            dictionary, optional (default = None)
            Dictionary holding all job informations. This dictionary has to
            contain a sub-dictionary for each job with the keys "point" and
            "DFT_idir". Have a look at the "_gather_jobs()" routine which can
            create these kinds of dictionaries. If None is passed, all SCF
            calculation from within <DFT_base_dir> (member variable) will be
            processed.

        ''**kwargs''
            Will be directly passed to the "calc_aim_cubes()" routine.

        Returns
        -------
        None
        """

        # make sure that the result_dir remains unchanged
        kwargs.pop('result_dir', None)

        starttime = time.time()

        # get the verbosity flag
        verbose = kwargs.pop('verbose', False)

        if jobs == None:
            if self.DFT_base_dir == None:
                print('You neither specified "jobs" nor the member variable "DFT_base_dir".')
                print('Consequently there are no jobs to be processed.')
                return None

            jobs = self._gather_jobs(self.DFT_base_dir,
                                     verbose = verbose)

        njobs = len(jobs.keys())
        nskipped = 0
        ncalculated = 0
        nprocessed = 0

        for point_str, ijob in sorted(jobs.items()):
            nprocessed += 1

            point = ijob['point']
            DFT_idir = ijob['DFT_idir']

            # get the job identifyer
            iseed = self.get_iseed(point)
            idir = self.get_idir(point)

            print(self._lim)
            print('LDFA-AIM calculation for seed: {}'.format(iseed))
            print('\tjob {} / {}'.format(nprocessed, njobs))
            print(self._lim)

            # skip directly if exists
            if os.path.exists(idir):
                # folder already exists...
                print('Skipping job "{}" due to existing files'.format(iseed))
                nskipped += 1
                continue

            # prepare the calculation
            self.prepare_continuation_calculation(DFT_idir = DFT_idir,
                                                  ijob_dir = idir,
                                                  iseed = iseed,
                                                  verbose = verbose)
            self.calc_aim_cubes(iseed = iseed,
                                elements = elements,
                                ijob_dir = idir,
                                verbose = verbose,
                                result_dir = 'cube_files',
                                **kwargs
                                )
            ncalculated += 1

        endtime = time.time()

        print(self._lim)
        print('Calculated : {0:>4d} / {1:d} jobs'.format(ncalculated, njobs))
        print('Skipped    : {0:>4d} / {1:d} jobs'.format(nskipped, njobs))
        print(self._lim)
        print('Runtime    : {}'.format(format_timing(starttime, endtime)))
        print(self._lim)

        return None


    def _read_aim_cube(self, cubefile, element, ni):
        """
        Function that reads an LDFA-AIM cube at the position specified by
        element and idx (see below).

        Parameters
        ----------
        ''cubefile''
            string
            The path to the cube file.

        ''element''
            string
            Element for which to read the AIM density.

        ''ni''
            integer
            CASTEP identifyer within a species ("ni"). This is used to
            distinguish different atoms of the same element. Note that the
            castep identifyer starts with 1 (Fortan-like).

        Returns
        -------
        AIM density at the position defined by <element> and <ni> in terms of
        the Wigner-Seitz radius in a.u.
        """

        icube = InterpolatedCube(cubefile,
                                 convert_cube_content = True,
                                 convert_to_rs = True)

        atoms = icube.get_atoms()

        # which atoms match the element (assume no reordering)
        idx = [a.index for a in atoms if a.symbol == element]

        # CASTEP uses Fortran enumeration, ie. starting with 1
        pos = atoms[idx][ni-1].position

        return icube(pos)


    def _read_data(self, base_dir = None, verbose = False):
        """
        Function that walks a given directory and parses the respective
        output files.

        Parameters
        ----------
        ''base_dir''
            string
            Path to the base directory. Defaults to the <self.base_dir> if None
            is given.

        ''verbose''
            boolean, optional (default = False)
            Print some more information to stdout.

        Returns
        -------
        Dictionary holding all information on the data. It is organized as
        follows:
            for every point:
            <point_str> : dictionary
                          Dictionary containg the information for the
                          individual points.
        """
        if base_dir is None:
            base_dir = self.base_dir

        # it is ensured that no user settings can change that!
        result_dir = 'cube_files'

        data = {}

        for path, dirs, files in os.walk(base_dir):
            if result_dir in dirs:
                # assume the prefix in get_idir --> hard coded in parent
                # only split at the first occurence, rest is done with
                # "_string_to_point()"
                point_str = os.path.basename(path).split('__',1)[-1]

                # convert to array of floats
                point = self._string_to_point(point_str)
                # get the point dictionary
                point_dict = self._point_to_dict(point)

                result_path = os.path.join(path, result_dir)

                for f in os.listdir(result_path):
                    pattern = r'.*-'+self._prefix+r'-(.*)\.cube\.gz'
                    match_obj = re.match(pattern, f)

                    if match_obj:
                        # which element and which species index...?
                        ispec = match_obj.groups()[-1]
                        pattern = r'([a-zA-Z]+)-ni_([0-9]+)'
                        element, ni = re.match(pattern, ispec).groups()
                        ni = int(ni)

                        # read the cube
                        if verbose:
                            print('Reading {}'.format(f))

                        f = os.path.join(result_path, f)
                        rho = self._read_aim_cube(f, element, ni)

                        point_dict['rho_aim_{}_{}'.format(element, ni)] = rho

                data[point_str] = point_dict

        return data


    def read(self, verbose = False):
        """
        Wrapper around a "_read_data()" routine which is to be written program-
        specific. The routine "_read_data()" shall return a dictionary holding
        sub-dictionaries (for each point) with all infomation in it.

        to an HDF-5 database at node '/raw_data/<self._prefix>'. Note that
        hyphens ("-") will be replaced by underscores ("_") to maintain the
        "natural naming" feature provided by pytables.

        Parameters
        ----------
        ''verbose''
            Boolean, optional (default = False)
            Print some additional information on the data (which jobs are
            pending and converged, respectively) to stdout.

        Returns
        -------
        Dataframe with the respective raw data
        """

        print('Reading data from:\n\t{}'.format(self.base_dir))
        print('Be patient...')

        data = self._read_data(base_dir = self.base_dir, verbose = verbose)

        print('Read {} points in total'.format(len(data.keys())))

        df = self.create_dataframe(data)
        update_hdf_node(df, '/raw_data/{}/'.format(self._prefix.replace('-','_')), self.store)

        return df
