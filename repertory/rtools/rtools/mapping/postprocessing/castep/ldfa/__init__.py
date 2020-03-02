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

from rtools.filesys import shell_stdouterr
from rtools.filesys import mkdir
from rtools.filesys import gzip_file
from rtools.helpers.pandashelpers import update_hdf_node
from rtools.mapping.postprocessing.castep import CastepCont

class LDFA(CastepCont):
    """
    Base class for the LDFA mapping routines (both AIM and IAA)

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
        # get the new keyword
        self.castep2cube_bin = self._get_binary(binary = kwargs.pop('castep2cube_bin', ''),
                                                name = 'castep2cube',
                                                default = 'castep2cube')

        # initialize the parent
        CastepCont.__init__(self, *args, **kwargs)


    def _get_binary(self, binary, default, name = 'n.a.'):
        """
        Function that checks for a given binary.

        Parameters
        ----------
        ''binary''
            string
            Path to the binary. If it evaluates to <False>, the <default> will
            be passed.
        
        ''default''
            string
            Default value, if <binary> evaluated to <False>.

        ''name''
            string, optional (default = 'n.a.')
            Binary name (IO only)
        
        Returns
        -------
        <binary> if it does not evaluate to False, <default> if so.
        """
        if binary:
            return binary
        else:
            return default
    

    def calc_cube(self, iseed,
                        ijob_dir, 
                        result_dir = 'cube_files', 
                        gzip = True, 
                        backup_existing = True, 
                        purge_existing = True,
                        init = True,
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
        
        ''init''
            boolean, optional (default = True)
            Check for requirements and create directories if necessary. Turn
            of, if you want to avoid double checking when using this routine in
            other routines.
        
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
            
            
        if init: 
            # check if all files are there...
            requirements = ['{}.{}'.format(iseed, suffix) for suffix in ('cell','param')] 
            self._check_requirements(requirements, ijob_dir)
            
            # make sure there is a proper result directory
            mkdir(result_dir, backup_existing = backup_existing, 
                              purge_existing = purge_existing, 
                              verbose = verbose) 
        if verbose: 
            print('Running cube calculation for seed: {}'.format(iseed))
            print('\tJob folder    : {}'.format(ijob_dir))
            print('\tResult folder : {}'.format(result_dir))
        
        # change to working directory
        os.chdir(ijob_dir)
        
        castep2cube_bin = self._link_binary(self.castep2cube_bin,
                                            verbose = verbose)
        
        castep2cube_str = r'{0} {1}'.format(castep2cube_bin, iseed)   
            
        if verbose:
            print('Running castep2cube:')
            print('\t' + castep2cube_str)
        
        shell_stdouterr(castep2cube_str) 
        
        # rename output 
        os.rename(iseed+'.chargeden_cube', iseed+'-chargeden.cube')
        
        # remove all unnecessary files
        if verbose:
            print('Removing unnecessary output files:')
        for f in os.listdir('.'):
            if re.search(r'_xsf_|_esp_|chdiff_cube|\.err', f):
                if verbose:
                    print('\t{}'.format(f))
                os.remove(f)
        
        outfile = iseed+'-chargeden.cube'
        
        if gzip:
            if verbose:
                print('Gzipping results')
            gzip_file(outfile)
            outfile += '.gz'
        

        if not os.path.samefile(ijob_dir, result_dir):
            if verbose:
                print('Moving results to resultfolder')
            shutil.move(outfile, result_dir)
        
        os.chdir(origin_dir)

