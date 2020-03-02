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

import re
import os

import numpy as np


try:
    import pandas as pd
    print('Pandas (+HDF5) support available')
except ImportError:
    print('Pandas (+HDF5) support *NOT* available')


class Mapping(object):
    """
    Generic mapping functionality.

    This is closely related to the Convergence class, and may at some point be
    merged with the latter.

    This is just the base class for any mapping. It has to be interfaced to the
    particular electronic structure code you are using and further adjusted for
    the particular task. Please, do not add any code or task specific routines
    to this class but rather make use of the power of object oriented
    programming. Add routines only if they are generic enough to work with more
    than one code.

    Initialization
    --------------
    ''seed''
        string
        Common seed for all caluclations. Usualy, this will be your system
        identifyer.

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

    # for io purposes
    _lim = '-'*80

    def __init__(self,
                 seed = None,
                 hdf5file = None,
                 base_dir = None,
                 point_names = None,
                 float_fmt = '+.3f'):

        # seed is mandatory
        # filter to not contain any multiple underscores
        self.seed = self._filter_separator(seed)

        if base_dir == None:
            self.base_dir = os.getcwd()
        else:
            self.base_dir = os.path.abspath(base_dir)

        if hdf5file != None:
            self._hdf5file = hdf5file
            try:
                self.store = pd.HDFStore(self._hdf5file)
            except AttributeError:
                pass

        if point_names != None:
            # again, filter to not contain any double underscores
            self.point_names = [self._filter_separator(n) for n in point_names]
        else:
            self.point_names = None

        self.float_fmt = float_fmt


    def __del__(self):
        """
        Do not forget to close the HDF5 store.
        """
        try:
            self.store.close()
        except AttributeError:
            pass

    def close(self):
        """
        Alias for destructor
        """
        self.__del__()


    def get_store(self):
        """
        Function that returns a pointer to the HDF store (if existing)
        """
        try:
            return self.store
        except AttributeError:
            return None

    def _filter_separator(self, string):
        """
        Remove any multiple underscores as they are used for separating
        purposes. Plus remove any leading or trailing underscores.

        Parameters
        ----------
        ''string''
            string
            String to be filtered

        Returns
        -------
        Filtered string (see above)
        """
        # remove multiple underscores
        string = re.sub(r'_{2,}', '_', string)

        # remove possibly leading underscore
        string = re.sub(r'^_', '', string)

        # remove possibly trailing underscore
        string = re.sub(r'_$', '', string)

        return string

    def _normalize_point(self, point):
        """
        Function which returns a numpy array of dtype float in any case, no
        matter whether point is a float, a string, an integer, or a list of
        something thereof.

        Parameters
        ----------
        ''point''
            float, int, list/np array thereof
            The point specifying the particular variables that are mapped.

        Returns
        -------
        np.ndarray of floats
        """

        if isinstance(point, float) or isinstance(point, int):
            return np.array([point], dtype = float)
        elif isinstance(point, list) or isinstance(point, np.ndarray):
            return np.array(point, dtype = float)


    def _point_to_string(self, point):
        """
        Return the string representation of a point "p1__p2__p3__...pn"
        The respective float format is given by the member variable 'float_fmt'

        Parameters
        ----------
        ''point''
            float, int, list/np array thereof
            The point specifying the particular variables that are mapped.
            Type conversion will be taken care of.

        Returns
        -------
        string as mentioned above
        """

        point = self._normalize_point(point)
        fmt_string = '{{0:{0:s}}}'.format(self.float_fmt)

        return '__'.join([fmt_string.format(p) for p in point])


    def _string_to_point(self, point_str):
        """
        Convert the string representation of a point to the respective numpy
        array. Returns a numpy array in any case, ie. no floats!

        Parameters
        ----------
        ''point_str''
            string
            String representation of a point as created with
            "_point_to_string()"

        Returns
        -------
        string as mentioned above
        """

        return np.array(point_str.split('__'), dtype = float)

    def _point_to_dict(self, point):
        """
        Function that returns a dictionary with point coordinates.
        Can be used in collecting data-routines.

        Parameters
        ----------
        ''point''
            numpy array/float
            The point coordinates. Will be passed through "_normalize_point()".

        Returns
        -------
        Dictionary with the individual point coordinates as values. The keys
        will be floats taken from "point_names" if passed upon intilialization,
        or "point_<i>" if not.
        """

        #make sure we have something iterable
        point = self._normalize_point(point)

        if self.point_names == None:
            point_names = ['point_{}'.format(i) for i in range(len(point))]
        else:
            point_names = self.point_names

        point_dict = {n : float(p) for n,p in zip(point_names, point)}

        return point_dict


    def get_iseed(self, point):
        """
        Create an individual seed for each calculation based on general seed
        and the point to be calculated.

        Parameters
        ----------
        ''point''
            float, int, list/np array thereof
            The point specifying the particular variables that are mapped.
            Type conversion and string normalization will be taken care of.

        Returns
        -------
        string consisting of <seed>{__x}* where <x> are the values in point.
        """

        iseed = self.seed + '__' + self._point_to_string(point)
        return iseed


    def get_idir(self, point, prefix = ''):
        """
        Create an individual directory name for each calculation based on
        the member variable 'base_dir' and the point to be calculated.

        Parameters
        ----------
        ''point''
            float, int, list/np array thereof
            The point specifying the particular variables that are mapped.
            Type conversion and string normalization will be taken care of.

        ''prefix''
            string
            Will be prepended to the point string representation (to avoid
            directories starting with '-' or '+'). If no prefix is given, the
            routine will try to read the member variable "_prefix". Hence, this
            can conveniently be modified for subclasses.

        Returns
        -------
        string consisting of <base_dir>/<prefix>{__x}* where <x> are the values in
        point.
        """
        if not prefix:
            #EAFP paradigm...
            try:
                prefix = self._prefix
            except AttributeError:
                pass

        if self.point_names != None:
            prefix = '_'.join([prefix] + self.point_names)

        prefix = self._filter_separator(prefix)

        if prefix != '':
            # now we can be sure that '__' is reserved for splitting purpose only
            prefix += '__'

        idir = os.path.join(self.base_dir, prefix + self._point_to_string(point))
        return os.path.abspath(idir)


    def read(self):
        raise NotImplementedError


    def create_dataframe(self, data):
        """
        Function that creates a pandas data frame. From a given data list.
        It takes care of proper dtypes for the respective columns.

        Arguments
        ---------
        ''data''
            Dictionary
            Dictionary holding all information on the data. It is to be
            organized as follows:

            for every point
            ---------------
            <point_str> : dictionary
                          Dictionary containg the information for the
                          individual points. It should in any case contain a
                          "point_dict" as obtained from "_point_to_dict()",
                          plus a further key should be the associated
                          observable. Further status variables may also be
                          used. Make sure that the proper types are assigned
                          already in these little sub-dictionaries!

        Returns
        -------
        Pandas DataFrame instance
        """

        # get the names and types from the first element of data
        tmp = data[0]
        names = tmp.keys()
        types = {n : type(tmp[n]) for n in names}
        columns = {n : [] for n in names}

        # get the single-type columns
        for idata in sorted(data):
            # note that idata are dictionaries
            for n in names:
                columns[n].append(idata[n])

        # create the dataframe
        df = pd.DataFrame()
        for n in names:
            df[n] = pd.Series(columns[n], dtype = types[n])

        return df


    def calculate(self, **kwargs):
        """
        Function that does the actual mapping, ie. sets all jobs and submits
        calculations.
        """

        raise NotImplementedError('"calculate()" has to be implemented by '
                                   'derived class')


