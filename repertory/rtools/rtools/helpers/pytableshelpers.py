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

#!/usr/bin/env python

"""
Tools for HDF5 database / pytables.

Author: Christoph Schober
"""

import tables
from contextlib import contextmanager
import rtools.filesys.lockfile as lockfile


@contextmanager
def open_file(path, *args, **kwargs):
    """
    Wrapper to open the pytables HDF5 database file with a file lock.

    Important: The file lock only works if open_file() is always used for
    write access to the database file.

    Parameters
    ----------
    path : str
        The filepath for the HDF5 database file
    mode : str
        The filemode to open the HDF5 file ("r", "w", "a", "r+")
    title : str
        The title for the tables.open method (-> Title of HDF5-table)
    **kwargs : dict
        Any other parameter valid for tables.open_file().

    Returns
    -------
    h5file : FileObject
        A pytables file object (see tables.open_file.__doc__ for details).

    Examples
    --------
    >>> from rtools.hdf5tools import open_file
    ... with open_file("database.h5", mode="r+", title="data") as h5file:
    ...     print(h5file.root)
    ...     # do pytables stuff, the file is locked now.

    """

    with lockfile.LockFile(path):
        try:
            h5file = tables.open_file(path, *args, **kwargs)
            yield h5file
        finally:
            try:
                h5file.close()
            except UnboundLocalError:
                pass
