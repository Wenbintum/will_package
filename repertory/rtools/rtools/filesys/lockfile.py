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
Lockfile provides functionality to lock and unlock files on UNIX/Linux for local
and NFS files.

Author: Christoph Schober
"""
import os
import subprocess
from contextlib import contextmanager


try:
    FNULL = open(os.devnull, 'w')
    s = subprocess.call(["lockfile"], stdout=FNULL, stderr=subprocess.STDOUT)
except OSError:
    raise RuntimeError("Could not find 'lockfile' binary. You can install\
 the tool with your favourite package manager (apt-get, aptitude, ...)")


class _LockBase(object):
    def __init__(self, name, locktimeout=600, sleeptime=8, retries=-1):

        self.path, self.filename = os.path.split(name)
        self.lockfile = self.filename+".lock"

        self.cmd_args = ["-"+str(sleeptime),
                         "-l", str(locktimeout),
                         "-r", str(retries),
                         os.path.join(self.path, self.lockfile)]
        self.cwd = os.getcwd()

    def __enter__(self):
        """
        Context manager support.
        """
        self.acquire()

    def __exit__(self, *_exc):
        """
        Context manager support.
        """
        self.release()

    def acquire(self):
        """
        Acquire a file lock.
        """
        raise NotImplemented("implement in subclass")

    def release(self):
        """
        Release an existing file lock.
        """
        raise NotImplemented("implement in subclass")

    def break_lock(self):
        """
        Remove a lock by force.
        """
        raise NotImplemented("implement in subclass")

    def is_locked(self):
        """
        Check if a lock exists.
        """
        raise NotImplemented("implement in subclass")


class LockFile(_LockBase):
    """
    Wrapper for ``lockfile`` and ``dotlockfile`` shell utilities to
    provide clean file lock. Pure Python implementations seem to
    suffer from stale file locks all the time.

    UNIX/Linux only! For details, see ``man lockfile`` or ``man dotlockfile``!

    Parameters
    ----------
    name : str
        The filename / path of the file to lock.
    sleeptime : int
        The time between two attempts to lock the file
    retries : int
        Number of retries to lock the file. -1 means retry forever
    locktimeout : int
        Remove lockfile by force after locktimeout seconds have passed.

    Returns
    -------

    Examples
    --------
    >>> lock = "somefile.txt"
    ... with lock:
    ...     with open("somefile.txt") as f:
    ...         f.write("lalala")
    """

    def acquire(self):
        err = subprocess.call(["lockfile"] + self.cmd_args)

    def release(self):
        os.remove(os.path.join(self.path, self.lockfile))

@contextmanager
def open_locked(name, *args, **kwargs):
    """
    Wrapper around the stdlib open() function to provide additional
    file lock when used.

    Important: The file lock only works if open_locked() is used!

    Full documentation for open(): open.__doc__ and file.__doc__!

    Parameters
    ----------
    name : str
        The filename / path of the file to open with a lock.

    **kwargs : dict
        Any parameters valid for the stdlib open() method.

    Returns
    -------
    fileobject : file
        A file object, identical to the normal open() method.

    Examples
    --------
    >>> with open_locked("somefile.txt") as f:
    ...     f.write("New line of data")


    """
    lock = LockFile(name)
    with lock:
        try:
            fileobject = open(name, *args, **kwargs)
            yield fileobject
        finally:
            fileobject.close()
