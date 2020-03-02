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

import textwrap
import time
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize


from rtools.filesys import mkdir
from rtools.mapping import Mapping
from rtools.helpers.pandashelpers import update_hdf_node

class PES(Mapping):
    """
    Mapping functionality for a potential energy surface (PES).

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
        Function which returns an ASE atoms object that returns the geometry of
        the system at the coordinates specified by `points`. This function must
        work on whichever input you later specify via the `points` argument and
        return a valid atoms object.

    ''get_calc''
        function
        Function that returns the respective ASE calculator. As for
        `get_atoms`, this function must not require any additional arguments.

    ''hdf5file''
        string, optional
        Path to a HDF5 database in which the results may be stored. Note that
        HDF5 support requires PyTables and Pandas!

    ''base_dir''
        string, optional (default: '.')
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
        # additional keywords that mapping itself does not carry
        # this will raise a KeyError if not there... just fine for me
        self.get_atoms = kwargs.pop('get_atoms')
        self.get_calc = kwargs.pop('get_calc')

        # the prefix for idir()
        self._prefix = 'PES'

        Mapping.__init__(self, *args, **kwargs)


    def _read_data(self, base_dir):
        raise NotImplementedError('"_read_data()" is program specific and has'
                ' to be implemented by derived class.')


    def read(self, base_dir = None, node = 'PES', verbose = False, process_resultfolder = None):
        """
        Wrapper around a "_read_data()" routine which is to be written program-
        specific. The routine "_read_data()" shall return a dictionary holding
        sub-dictionaries (for each point) with all infomation in it.

        to an HDF-5 database at node '/raw_data/PES'.

        Parameters
        ----------
        ''base_dir''
            string, optional (default = <self.base_dir>)
            Path to the base directory. Defaults to the standard <base_dir> but
            can be changed if you want to read e.g. a testset.

        ''node''
            string, optional (default = 'PES')
            Node name for the HDF5 database.

        ''verbose''
            Boolean, optional (default = False)
            Print some additional information on the data (which jobs are
            pending and converged, respectively) to stdout.

        Returns
        -------
        Dataframe with the respective raw data
        """

        if base_dir is None:
            base_dir = self.base_dir

        data = self._read_data(base_dir = base_dir, process_resultfolder = process_resultfolder)

        df = self.create_dataframe(data)

        finished = df[df['converged']]
        pending = df[~df['converged']]

        njobs =  len(df)
        nfinished = len(finished)
        npending = len(pending)

        if verbose:
            print(self._lim)
            print('*** Finished jobs ({} / {}) ***'.format(nfinished, njobs))
            print(self._lim)
            print(finished)
            print(self._lim)
            print('*** Pending jobs ({} / {}) ***'.format(npending, njobs))
            print(self._lim)
            print(pending)
        print(self._lim)
        print('*** Finished {} of {} jobs ***'.format(nfinished, njobs))
        print(self._lim)

        update_hdf_node(df, '/raw_data/{}'.format(node), self.store)

        return df


    def analyze_database(self, node='PES'):
        """
        Function that basically just normalizes the energies in the database
        and stores it in '/analysis/PES'.

        Parameters
        ----------
        ''node''
            string, optional (default = 'PES')
            Node name for the HDF5 database. Note that this has to be the same
            as for the raw data.

        Returns
        -------
        Dataframe
        """
        df = self.store['/raw_data/{}'.format(node)]
        df['energy_normalized'] = df['energy'] - np.min(df['energy'])
        update_hdf_node(df, '/analysis/{}'.format(node), self.store)

        return df


    def write_ascii(self, node='PES',
                          observable='energy_normalized',
                          fname='PES.dat',
                          comment='no unit info provided',
                          include_points=True,
                          **kwargs):

        """
        Routine to actually dump things from the database to a clear-text ascii
        file.

        Parameters
        ----------
        ''node''
            string, optional (default = 'PES')
            The node that is to be considered. It will be '/analysis/<node>',
            as we do not want raw data dumping to clear text. This is what the
            HDF5 database is for.

        ''observable''
            string/list of strings, optional (default = 'energy_normalized')
            The column in the dataframe that is printed next to the respective
            coordinates. Can also be a list of strings for several output
            quantities.

        ''fname''
            string, optional (default = 'PES.dat')
            The filename to be written to. You can specify an entire path as
            well, folders will be created on demand.

        ''comment''
            string, optional (default = 'no unit info provided')
            Some string that comments on the data in the file. This is up to
            the user.

        ''include_points''
            boolean, optional (default=True)
            Include the point identifyer, even if not specified as observable
            (fallback mode)

        **kwargs
            Passed to the dataframe.to_string() method. Allows more finegrained
            control on the format.

        Returns
        -------
        <None>
        """
        # check if we need to create the directory
        dirname = os.path.dirname(fname)
        if dirname:
            mkdir(dirname, backup_existing = False,
                           purge_existing = False,
                           verbose = False)

        df = self.store['/analysis/{}'.format(node)]

        if not isinstance(observable, list):
            observable = [observable]

        if include_points:
            idx = self.point_names + observable
        else:
            idx = observable

        print('Writing data to ascii file : {}'.format(fname))
        print('\tObservable(s):\n\t* {}'.format('\n\t* '.join(observable)))
        with open(fname, 'w') as f:
            f.write('# {}'.format(f.name))
            f.write('\n# file written on: {}'.format(time.strftime('%c')))
            if comment:
                f.write('\n#')
                comment = comment.split('\n')
                for c in comment:
                    for line in textwrap.wrap(c, width=78):
                        f.write('\n# {}'.format(line))

            data='#' + df[idx].to_string(index=False, **kwargs)[1::]
            f.write('\n#\n#\n{}'.format(data))


    def create_testset_single_minimum(self, interpolation_function,
                                            interpolation_range,
                                            minimum = None,
                                            testset_size = 30,
                                            Elim = None,
                                            _sigma = 3.):
        """
        Function that creates a testset on a given interpolation function.
        The points will be distributed according to a gaussian normal
        distribution around the minimum of the PES. The expectation value will
        be the minimum coordinate and the standard deviation will be sigma =
        len(<interpolation_range>) / 3., which causes 99.8% of all drawn points
        to be within the interpolation range.  However, there is a further
        check if the point is actually in the range.

        See also:
        http://en.wikipedia.org/wiki/Standard_deviation#Rules_for_normally_distributed_data


        Parameters
        ----------
        ''interpolation_function''
            function
            Interpolation function. To be called with a (ndim x 1) array.

        ''interpolation_range''
            (ndim x 2) array
            Array specifying the inerpolation range for each dimension.

        ''minimum''
            array, optional (default = None)
            The minimum of the potential. If none is given, the routine will
            try to minimize the potential.

        ''testset_size''
            integer, optional (default = 30)
            Size of the generated testset

        ''Elim''
            float, optional (default = None)
            If given, only points with interpolation_function(point) < "Elim"
            will be added to the testset.

        ''_sigma''
            float, optional (default = 3.)
            '_sigma' in sigma = 1/_sigma * interpolation_range for the standard
            deviation.

        Returns
        -------
        List of <testset_size> points that satisfy the specifyed criteria.
        """

        # get the dimensionality from the interpolation range
        ndim = interpolation_range.shape[0]

        # Find the minimum using scipy, start with zeros as guess
        if minimum is None:
            minimum = minimize(interpolation_function,
                               x0 = np.zeros(ndim),
                               options = {'disp' : False})['x']

        # upper boarder is infinity if nothing is passed
        if Elim == None:
            Elim = np.inf

        #check for interpolation ranges
        ranges = abs(np.diff(interpolation_range)).flatten()

        testset = []

        while len(testset) < testset_size:
            point = np.random.randn(ndim)*ranges / _sigma + minimum
            # is the point within the interpolation interval?
            if np.any(point <= np.min(interpolation_range, axis = 1)):
                continue
            if np.any(point >= np.max(interpolation_range, axis = 1)):
                continue
            if interpolation_function(point) <= Elim:
                testset.append(point)

        return testset


