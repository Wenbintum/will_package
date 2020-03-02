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
Set of helper tools to organize data with pandas.
Rather customized routines, though.

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

import numpy as np
import textwrap
import os
import time
import re

from rtools.filesys import mkdir_p

import pandas as pd
from pandas.util.testing import assert_frame_equal

def _transform_datalist_to_arrays(data):
    """
    Transform data given as list of tuples

        (index, value, exists, finished, converged)

    of type

        (str, float, bool, bool, bool)

    to three arrays

        index, value, status

    of proper datatype. This allows to avoid object-like arrays with string
    representation for bools and floats, and allows for convenient slicing.

    Such data lists occur from time to time when parsing lots of data. The str
    component is some index, the flaot value is the target quantity and the
    booleans are status bits.

    This routine is very customized, hence it is private. Feel free to add a
    generic routine ;)

    Parameters
    ----------
    data : N-length list of tuples (str, float, bool, bool, bool)
        Input data as described above.

    Returns
    -------
    index : (Nx1) array with dtype=str
        String component of the tuples above.

    value : (Nx1) array with dtype=float
        Float component of the tuples above

    status : (Nx3) array with dtype=bool
        Boolean components of the tuples above.
    """

    index = []
    value = []
    status = []
    for var, val, exists, finished, converged in data:
        index.append(var)
        value.append(float(val))
        status.append(np.array([exists, finished, converged], dtype = bool))

    return (np.array(index, dtype=str),
            np. array(value, dtype=float),
            np.array(status,dtype=bool))

def _transform_generic_datalist_to_arrays(data):
    """
    Transform data given as list of tuples

        (index, value, exists, finished, converged)

    of type

        (str, array, bool, bool, bool)

    to three arrays

        index, values, status

    of proper datatype. This allows to avoid object-like arrays with string
    representation for bools and floats, and allows for convenient slicing.

    Such data lists occur from time to time when parsing lots of data. The str
    component is some index, the flaot value is the target quantity and the
    booleans are status bits.

    This routine is very customized, hence it is private. Feel free to add a
    generic routine ;)

    Parameters
    ----------
    data : N-length list of tuples (str, float-array, bool, bool, bool)
        Input data as described above.

    Returns
    -------
    index : (Nx1) array with dtype=str
        String component of the tuples above.

    values : (Nxn) array with dtype=float
        Float components of the tuples above

    status : (Nx3) array with dtype=bool
        Boolean components of the tuples above.
    """

    index = []
    values = []
    status = []
    for var, val, exists, finished, converged in data:
        index.append(var)
        values.append(np.asarray(val, dtype=float))
        status.append(np.array([exists, finished, converged], dtype = bool))

    return (np.array(index, dtype=str),
            np. array(values, dtype=float),
            np.array(status,dtype=bool))

def create_pandas_dataframe(data, column_names, index_name = None):
    """
    Routine to create a pandas data frame from data as described in
    _transform_datalist_to_arrays().

    Again, this is rather customized. But I seed no chance and sense to
    implement it more generically.

    Parameters
    ----------
    data : N-length list of tuples (str, float, bool, bool, bool)
        Input data. The str component will become the data frame index.

    column_names : 4-length list of strings, optional
        Names for the respective columns, i.e. the flaot and bool components of
        the input data. If not specified, this will default to

            ['observable', 'status1', 'status2', 'status3']

    index_name : str, optional
        Name of the data frame index.

    Returns
    -------
    df : pandas dataframe
        Data frame with the input data.
    """

    # first transform the data
    index, value, status = _transform_datalist_to_arrays(data)

    if column_names is None:
        column_names = ['observable',
                        'status1',
                        'status2',
                        'status3']

    df = pd.DataFrame(columns = column_names, index = index)

    if index_name:
        df.index.name = index_name

    # the float component
    df[column_names[0]] = pd.Series(value, index = index)

    # the boolean components
    for i, key in enumerate(column_names[1::]):
        df[key] = pd.Series(status[:,i], index = index)

    return df

def create_generic_pandas_dataframe(data,
                                    observable_name='observable',
                                    status_names=['status1', 'status2', 'status3'],
                                    index_name = None):
    """
    Routine to create a pandas data frame from data as described in
    _transform_generic_datalist_to_arrays().

    Again, this is rather customized. But I seed no chance and sense to
    implement it more generically.

    Parameters
    ----------
    data : N-length list of tuples (str, float array, bool, bool, bool)
        Input data. The str component will become the data frame index.

    observable_name : str, optional
        Names for the respective observable columns

    status_names: str, optional
        Names for the three status integers.

    index_name : str, optional
        Name of the data frame index.

    Returns
    -------
    df : pandas dataframe
        Data frame with the input data.
    """

    # first transform the data
    index, values, status = _transform_generic_datalist_to_arrays(data)

    Nsteps, i, j = values.shape
    Nelements = i*j

    column_names = []
    for _i in range(i):
        for _j in range(j):
            column_names += ['{}_{}_{}'.format(observable_name, _i, _j)]
    column_names += status_names

    df = pd.DataFrame(columns = column_names, index = index)

    if index_name:
        df.index.name = index_name

    values = values.reshape(Nsteps,-1)

    # the float component
    for i, key in enumerate(column_names[0:Nelements]):
        df[key] = pd.Series(values[:,i], index = index)

    # the boolean components
    for i, key in enumerate(column_names[Nelements:]):
        df[key] = pd.Series(status[:,i], index = index)

    return df

def create_pandas_dataframe_from_array(array, column_names=None):
    """
    Create a dataframe from a generic array. Of course, all data has to be of
    the same type.


    Parameters
    ----------
    array : (N, M) array
        Input data.

    column_names : (N) list, optional (default=None)
        Names for the respective columns. Defaults to ["col_X",...]

    Returns
    -------
    df : pandas dataframe
        Data frame with the input data.
    """
    array = np.asarray(array)

    if column_names is None:
        column_names = ["col_{}".format(i) for i in range(array.shape[1])]


    df = pd.DataFrame(columns = column_names)

    # the boolean components
    for i, key in enumerate(column_names):
        df[key] = pd.Series(array[:,i])

    return df




def update_hdf_node(df, node, store):
    """
    Update a given hdf5 node with a pandas dataframe.

    If node in the file is unchanged, nothing will be written to the HDF5store.

    Parameters
    ----------
    df : Pandas data frame
        Data frame that is supposed to be written to the HDF5Store.

    node : str
        Node at which to write to the HDF5Store.

    store : pandas.HDF5Store instance
        HDF5Store at which to write.
    """

    try:
        old_df = store[node]
        assert_frame_equal(df, old_df)
    except:
        print('updating store: {}\n\tnode: {}'.format(store.filename, node))
        store.put(node, df)

    return None


def write_df_to_txt(df, filename, info=None, verbose=True, **kwargs):
    """
    Write a dataframe to a formatted ascii file.

    Parameters
    ----------
    df : Pandas dataframe object
        The dataframe to be written.

    filename : str
        File to write to (mode 'w'). Directories will be created as required.

    info : str, optional (default=None)
        Additional information that shall be written to the file. Will be
        wrapped to line length of 78, and each line will be prepended a hash
        tag '#'.

    verbose: bool, optional (default=True)
        Print some status information or not.

    **kwargs
        Directly forwared to pandas' DataFrame.to_string() method.
    """
    #print(os.path.dirname(filename))
    mkdir_p(os.path.dirname(os.path.abspath(filename)))

    with open(filename, 'w') as f:
        if verbose:
            print('Dumping dataframe to:\n\t{}'.format(f.name))
        f.write('# {}\n# File written on {}\n#'.format(os.path.basename(f.name), time.strftime('%c')))
        if info is not None:
            for i in info.split('\n'):
                lines = textwrap.wrap(i.strip().replace('#',''), width=76)
                # catch paragraphs
                if len(lines) == 0:
                    f.write('\n#')
                else:
                    for l in lines:
                        f.write('\n# {}'.format(l))
            f.write('\n#')
        f.write(_format_df(df.to_string(**kwargs)))

    return None

def _format_df(content):
    """
    some additional cosmetics to what is returned from df.to_string
    """
    head_elems = [s.strip() for s in content.split('\n')[0][1:].split()]
    index = content.split('\n')[1].strip()

    if index:
        # length of the elements
        head_lens = [len(index)+2] + [len(e) for e in head_elems]
    else:
        head_lens = [len(head_elems[0])+2]
        if len(head_elems) != 1:
            head_lens += [len(e) for e in head_elems[1:]]

    data_lens = [len(s.strip()) for s in content.split('\n')[2].split()]
    cols_lens = [max(i,j) for i, j in zip(head_lens, data_lens)]

    template = '\n' + '     '.join(['{{:{len}s}}'.format(len=l) for l in cols_lens])

    if index:
        head = template.format('# ' + index, *head_elems)
    else:
        head_elems[0] = '# '+head_elems[0]
        head = template.format(*head_elems)

    body = '\n#'+'-'*(len(head) - 2)
    body += head
    body += '\n#'+'-'*(len(head) -2)

    data = content.split('\n')[2:]
    for line in sorted(data):
        body += template.format(*line.split())

    return body



