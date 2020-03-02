import os

from rtools.cube import InterpolatedCube
from rtools.helpers.pandashelpers import update_hdf_node
from rtools.mapping.postprocessing.castep.ldfa import LDFA


class IAA(LDFA):
    """
    Class to map LDFA-IAA friction coefficients based on existing SCF
    calculations.
    
    Initialization
    --------------
    ''seed'' 
        string
        Common seed for all calculations. Usualy, this will be your system
        identifyer.
    
    ''get_atoms''
        function
        Function which returns an ASE atoms object that returns the geometry of
        the system at the coordinates specified by `points`. This function must
        work on whichever input you later specify via the `points` argument and
        return a valid atoms object.
    
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
    
    _logo = r"""
--------------------------------------------------------------------------------
                  ____          _            ___    _        _    
                 / ___|__ _ ___| |_ ___ _ __|_ _|  / \      / \   
                | |   / _` / __| __/ _ \ '_ \| |  / _ \    / _ \  
                | |__| (_| \__ \ ||  __/ |_) | | / ___ \  / ___ \ 
                 \____\__,_|___/\__\___| .__/___/_/   \_\/_/   \_\
                                       |_|                        

                        Simon P. Rittmeyer, TUM, 2015
                          simon.rittmeyer(at)tum.de
--------------------------------------------------------------------------------
"""[1:-1]

    def __init__(self, *args, **kwargs):
        
        # additional keywords that mapping itself does not carry
        # this will raise a KeyError if not there... just fine for me 
        self.get_atoms = kwargs.pop('get_atoms')
        
        self._prefix = 'LDFA-IAA'
        
        self.cs_dir = kwargs.pop('cs_dir', None)
        if self.cs_dir is None:
            raise ValueError('Variable "cs_dir" not initialized')

        # initialize the parent
        LDFA.__init__(self, *args, **kwargs)

        print(self._logo)
   

    def calc_cs_cube(self, verbose = False):
        """Wrapper around calc_cube and respective preparation, but geared
        towards clean surface calculations only"""
        
        job_dir = os.path.join(self.base_dir, 'clean_surface')
        seed = self.seed + '_CLEAN_SURFACE'

        # prepare the calculation
        self.prepare_continuation_calculation(DFT_idir = self.cs_dir,
                                              ijob_dir = job_dir,
                                              iseed = seed,
                                              verbose = verbose)
        self.calc_cube(iseed = seed,
                       ijob_dir = job_dir,
                       result_dir = 'cube_files',
                       init = True,
                       gzip = True,
                       verbose = verbose)


    def _interpolate_cs_cube(self, cubefile):
        """
        Return the interpolated clean surface density
        """
        cs_cube = InterpolatedCube(cubefile,
                                   convert_cube_content = True,
                                   convert_to_rs = True,
                                   precalc_weights = True)
        return cs_cube


    def read(self, points, atoms_idx, atoms_names, verbose = False):
        """
        Loop over all points and read the electronic density of the clean
        surface at these points
        """

        # we can hard-code it here
        cs_cubefile = os.path.join(self.base_dir, 'clean_surface', 'cube_files', 
                                   self.seed + '_CLEAN_SURFACE' + '-chargeden.cube.gz') 
        
        if not os.path.exists(cs_cubefile):
            self.calc_cs_cube(verbose = verbose)
        
        cs_cube = self._interpolate_cs_cube(cs_cubefile)
        
        data = {}

        for point in points:
            
            point_str = self._point_to_string(point)
            point_dict = self._point_to_dict(point)
            
            positions = self.get_atoms(point).get_positions()
            for idx, name in zip(atoms_idx, atoms_names):
                pos = positions[idx]

                point_dict['rho_iaa_{}'.format(name)] = cs_cube(pos)

            data[point_str] = point_dict

    
        df = self.create_dataframe(data)
        update_hdf_node(df, '/raw_data/{}/'.format(self._prefix.replace('-','_')), self.store)
        
        return df

