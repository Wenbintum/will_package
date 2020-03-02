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
Collection of useful tools to replace command line *nix functionality.

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

from __future__ import absolute_import, print_function

import os
import errno
import fnmatch
import sys
import shutil
import tarfile
import time
import gzip
import subprocess


def gzip_file(filename, delete_original = True):
    """
    Function that gzips a file just like the corresponding command lines tool.
    Yet, this routine is pure-python.

    Parameters
    ----------
    ''filename''
        string
        The file to be compressed. Note that the latter will be deleted after
        compression, analogous to the command line tool, if "delete_original =
        True".

    ''delete_original''
        Boolean, optional (default = True)
        Whether the original files is to be deleted (like command line tool) or
        not.

    Returns
    -------
    None

    ---
    Simon P. Rittmeyer
    simon.rittmeyer(at)tum.de
    """

    with open(filename, 'rb') as f_in:
        with gzip.open(filename + '.gz', 'wb') as f_out:
            f_out.writelines(f_in)

    if delete_original:
        os.remove(filename)


def mkdir(path,
          backup_existing = True,
          purge_existing = False,
          verbose = False):
    """
    Routine that creates a given directory.

    Arguments
    ---------
    ''path''
        string
        Path of the desired directory.

    ''backup_existing''
        Boolean, optional (default: True)
        If True, there is no particular treatment of possibly exisiting
        directories. This may cause data loss, so be careful.
        If False, the content of an already existing directory will be
        backup-ed to `bak_YYYY-MM-DD--HH-MM-SS.tgz` within the required
        directory.

    ''purge_existing''
        Boolean, optional (default = False)
        Delete anything except from the backup archives from within <path> (if
        existing). *Handle with care*.

    ''verbose''
        Boolean, optional (default : False)
        Print some information to stdout.

    Returns
    -------
    ''status''
        Boolean
        `True` if folder was created, `False` if folder already existed.

    ---
    Simon P. Rittmeyer
    simon.rittmeyer(at)tum.de
    """
    path = os.path.abspath(path)

    if os.path.exists(path):
        msg = 'Folder already exists:\n\t{}'.format(path)
        if os.listdir(path):
            if backup_existing:
                tarball = 'bak_{}.tgz'.format(time.strftime("%Y-%m-%d--%H-%M-%S"))
                msg += '\n\t-> Saving content to archive {}'.format(tarball)
                with tarfile.open(os.path.join(path, tarball), 'w:gz') as tb:
                    for f in os.listdir(path):
                        fbase = os.path.basename(f)
                        if not fbase.startswith('bak__'):
                            tb.add(os.path.join(path, f))
            else:
                if not purge_existing:
                    msg += '\n\t-> Ignore any existing files in this folder. This may cause data loss, be careful!'

            if purge_existing:
                msg +='\n\t-> Deleting content (except from bak_*.tgz archives)'
                for f in os.listdir(path):
                    if f.startswith('bak_') and f.endswith('.tgz'):
                        continue
                    f = os.path.join(path, f)
                    if os.path.isdir(f):
                            shutil.rmtree(f)
                    else:
                        os.remove(f)

        status = False

    else:
        msg = 'Created folder:\n\t{}'.format(path)
        os.makedirs(path)
        status = True

    if verbose:
        print(msg)

    return status


def shell_stdouterr(raw_command):
    """
    Abstracts the standard call of the commandline, when
    we are only interested in the stdout and stderr. Taken from
    ase.calculators.castep.

    Parameters
    ----------
    ''raw_command''
        string
        The command string to be executed on the command line.

    Returns
    -------
    (stdout, stderr)-tuple containing the standard out/error stream due to the
    command.
    """
    stdout, stderr = subprocess.Popen(raw_command,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True).communicate()

    return stdout.strip(), stderr.strip()


def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.
    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    !!! Monkey-patched utility from Python 3.3 shutil module !!!
    """
    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return (os.path.exists(fn) and os.access(fn, mode)
                and not os.path.isdir(fn))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to the
    # current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if not os.curdir in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if not normdir in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None


def in_directory(file, directory, resolve_symlinks=True, expand_vars=True):
    """
    Returns True if "file" is within a subdirectory of "directory".

    Parameters
    ----------
    file : str
        A filename or directory
    directory : str
        A directory
    resolve_symlinks : Bool
        If True, symbolic links in paths are expanded
    expand_vars : Bool
        If True, variables in paths are expanded
    """
    if expand_vars:
        directory = os.path.expandvars(directory)
        file = os.path.expandvars(file)
    directory = os.path.abspath(os.path.expanduser(directory))
    file = os.path.abspath(os.path.expanduser(file))
    if resolve_symlinks:
        directory = os.path.realpath(directory)
        file = os.path.realpath(file)
    directory = os.path.join(directory, "")
    return os.path.commonprefix([file, directory]) == directory


def mkdir_p(path):
    """
    Creates directory with parent directories as needed
    (similar to 'mkdir -p ${path}').
    Does not raise an error if directory already exists.

    Parameters
    ----------
    path : str
        A directory name
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise e
    return


def _fnmatch_incl_excl(item, ipattern, xpattern):
    """
    Returns True when 'item' matches
        - at least one of the patterns in 'ipattern'
    and
        - not a single pattern in 'xpattern'.
    Returns False otherwise.
    The fnmatch.fnmatch() function is used to determine matches. It can
    handle wildcards, see http://docs.python.org/2.6/library/fnmatch.html

    Parameters
    ----------
    item : str
    ipattern : iterable
        include patterns
    xpattern : iterable
        exclude patterns

    Returns
    -------
    bool
    """
    return (any(fnmatch.fnmatch(item, _pi) for _pi in ipattern) and
            all(not fnmatch.fnmatch(item, _px) for _px in xpattern) )


def copy_r(source, dest,
        include_files=['*'], exclude_files=[],
        include_dirs=['*'], exclude_dirs=[],
        preserve_metadata=True,
):
    """
    Make a copy of 'source' and its content to 'dest'.

    Parameters
    ----------
    source : str
        source file or directory
    dest : str
        file or directory as destination
    include_files : list
        include filenames pattern (recognized by fnmatch)
    exclude_files : list
        exclude filenames pattern (recognized by fnmatch)
    include_dirs : list
        include directory names pattern (recognized by fnmatch)
    exclude_dirs : list
        exclude directory names pattern (recognized by fnmatch)
    preserve_metadata : bool
        If True, metadata is copied as well for every file
    """
    # walk through the directory dir top to bottom
    for src_dir, dirs, files in os.walk(source, topdown=True):
        # get relative path of current dir to source
        rel_dir = os.path.relpath(src_dir, source)
        # assure that the dest directory exists
        dest_dir = os.path.join(dest, rel_dir)
        mkdir_p(dest_dir)
        if preserve_metadata:
            shutil.copystat(src_dir, dest_dir)
        # copy the (filtered) files
        for f in files:
            if _fnmatch_incl_excl(f, include_files, exclude_files):
                src = os.path.join(src_dir, f)
                des = os.path.join(dest_dir, f)
                shutil.copyfile(src, des)
                if preserve_metadata:
                    shutil.copystat(src, des)
        # overwrite dirs to exclude directories that shall not be copied,
        # os.walk will then ignore them
        dirs[:] = [_d for _d in dirs
            if _fnmatch_incl_excl(_d, include_dirs, exclude_dirs)
        ]
    return

