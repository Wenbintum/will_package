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
Helpers to manipulate python environments such as
    sys.path
    os.environ
    ...

General remark:
---------------
The following functions operate only on the local environment, i.e.
the global environment variables are not changed.



Author: Markus Sinstein, 2016

"""

from __future__ import print_function

import sys
import os

from rtools.filesys import in_directory

def clear_pythonpath_of_dir(remove_dirs, resolve_symlinks=False):
    """
    Remove entries from sys.path which start with any string in
    the list "remove_dirs".

    Parameters
    ----------
    remove_dirs : str / iterable of str
        Starting pattern(s) to be removed from sys.path
    resolve_symlinks : Bool
        Passed to rtools.filesys.in_directory

    Examples
    --------
    To prohibit the import of python libraries from certain directories like
    custom compiled modules in the user's home directory, call

    >>> clear_pythonpath_of_dir("~")

    before importing modules in your program. Following import calls
    will ignore the home directory, as all corresponding entries
    have been removed from sys.path.
    """
    if isinstance(remove_dirs, str):
        dirs = (remove_dirs,)
    else:
        dirs = remove_dirs
    for d in dirs:
        for i in range(len(sys.path)-1,-1,-1):
            if in_directory(sys.path[i], d, resolve_symlinks=resolve_symlinks):
                del sys.path[i]


if __name__=="__main__":
    from argparse import ArgumentParser
    from copy import copy

    parser = ArgumentParser(description="""
Remove all entries from the PYTHONPATH variable
that start with a given <prefix>, i.e. "/user/anonymous/".
"""[1:-1])
    parser.add_argument("prefixes",
        action="store", type=str, nargs="*", default="~",
        help="defaults to the current user's home directory")
    parser.add_argument("-v", "--verbose",
        action="store_true",
        help="verbose mode")

    args = parser.parse_args()

    path_before = copy(sys.path)
    clear_pythonpath_of_dir(args.prefixes)
    if args.verbose:
        indent_del = "--- "
        indent_kep = "    "
        print("PYTHONPATH (entries with {} have been deleted)".format(indent_del))
        for p in path_before:
            indent = indent_kep if p in sys.path else indent_del
            print("{indent}{p}".format(p=p, indent=indent))

