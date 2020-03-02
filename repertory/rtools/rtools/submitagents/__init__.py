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
import importlib
import os
import sys
import warnings
import re

# python 2/3 transition
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser

from collections import MutableSequence, MutableMapping

from copy import copy

from rtools.misc import get_close_matches


class _AddList(MutableSequence):
    def __init__(self, *args, **kwargs):
        self._list = list(*args)

    def insert(self, key, value):
        self._list.insert(key, value)

    def __setitem__(self, i):
        self._list.append(i)

    def __getitem__(self, i):
        return self._list[i]

    def __len__(self):
        return len(self._list)

    def __delitem__(self, i):
        """Delete an item"""
        del self._list[i]
        return

    def __repr__(self):
        return str(self._list)

    def add(self, item):
        self._list.append(item)

    def remove(self, i):
        self.__delitem__(i)


class _AddDict(MutableMapping):
    """
    The _AddDict dictionary with Add and Remove.
    """
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        if key in self.store:
            self.store[key].append(value)
        else:
            self.store[key] = [value]

    def __delitem__(self, key):
        del self.store[key]

    def __delvalue__(self, key, idx):
        self.store[key].get(idx)

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return str(self.store)

    def add(self, key, value):
        self.__setitem__(key, value)

    def remove(self, key, value=None):
        if value is None:
            self.__delitem__(key)
        else:
            for num, item in enumerate(self.__getitem__(key)):
                if value == item:
                    self.__delvalue__(key, num)

class FakeSecHead(object):
    """
    Fake sections header in file (to use it for the default files).

    Taken from
        http://stackoverflow.com/a/2819788
    """
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()


def check_email_address(email_address):
    """
    check for valid mail format
    """
    mail_pattern = r'[\w_\-\.]+@[\w_\-]+\.[\w]'

    if not re.search(mail_pattern, email_address):
        raise RuntimeError('Invalid user mail address does not match r"{}"'.format(mail_pattern))
    else:
        return True


class Agent(object):
    """
    Base-class for all submitagents for different codes/tasks.

    An agent is supposed to handle the task of creating and
    submitting a job file to l super computer/cluster (PBS and SLURM so far
    queuing).

    ---
    Christoph Schober, Simon P. Rittmeyer (TUM), 2015-2016.
    """

    def __init__(self, **kwargs):
        """
        Here we just create the very basic things such as the command structure
        and the parameter validation. Any further things have to be implemented
        by subclasses.

        Passing init_params=False will skip the paramter initialization.
        """
        init_params = kwargs.pop('init_params', True)

        self._precmd = _AddList(kwargs.pop("precmd",list()))
        self._cmd = _AddList()
        self._postcmd = _AddList(kwargs.pop("postcmd",list()))
        self._environment = _AddDict()
        self._setupcommands = _AddList()
        self._params = {}

        self._params_initialized = False

        if init_params:
            self._init_params(kwargs)


    @property
    def defaults(self):
        try:
            return self._defaults
        except AttributeError:
            warnings.warn('Dictionary "self.defaults" not implemented. Will use an empty dictionary!')
            return {}

    @defaults.setter
    def defaults(self, value):
        # This construct allows to define self._defaults in children, which is
        # overwrites the ones defined in the parents.
        try:
            value.update(self._defaults.copy())
        except AttributeError:
            pass
        self._defaults = value

    @property
    def required(self):
        try:
            return self._required
        except AttributeError:
            warnings.warn('List "self.required" not implemented. Will use an empty list!')
            return []

    @required.setter
    def required(self, value):
        # similar as for defaults, but a set is enough here
        try:
            self._required += value
            self._required = list(set(self._required))
        except AttributeError:
            self._required = list(set(value))



    def _init_params(self, kwargs):
        """
        Initialize parameters given through kwargs. Note that you should
        implement two things in your subclass:

        * a dictionary "self._defaults" that contains *all* possible user-set
          parameters that may be changed via kwargs.

        * a list "self._required" that contains parameters that must be present
          in kwargs and must not be None.

        This routine then fills the internal "self._params" dictionary which
        holds all active settings. In doing so, it is verified that no unknown
        arguments are passed and that the reqirements specified above are met.
        Otherwise an Error will be raised.
        """
        # make sure that we have all of them
        self._all_keys = set(list(self.defaults.keys()) + list(self.required))

        # fill in defaults from the file
        # the settings in the defaultfile override the hard-coded class
        # defaults, but still user settings will be respected.
        ignore_defaultfile = kwargs.pop('ignore_defaultfile', False)

        if not ignore_defaultfile:
            self.parse_defaultfile()

        self._params = copy(self.defaults)
        for key, value in kwargs.items():
            if self._check_arg(key) is True:
                self.params[key] = value

        # jsut check for required arguments
        self._check_required()


        # just some convenience flag
        self._params_initialized = True


    def _check_arg(self, arg):
        """
        Test if argument is known in defaults, if not, return similar keys.
        """
        if arg in self._all_keys:
            return True
        else:
            alternatives = get_close_matches(arg, self._all_keys)
            if alternatives == '':
                raise RuntimeError("Could not find option '{0}' or any similar key".format(arg))
            else:
                raise RuntimeError("Could not find option '{0}'.\n {1}".format(
                    arg, alternatives))


    def _check_required(self, tolerate_None=False):
        """
        Check if any of the "self._required" arguments is either not present in
        "self.params" or evaluates to <None>. In case "self._required" does not
        exist, an empty list will be used.

        Parameters
        ----------
        tolerate_None : bool, optional (default=False)
            Just check for presence of arguments, no values.

        Returns
        -------
        <True> if "params" complies with "required".

        Raises
        ------
        <ValueError> if "self._params" does not comply with "self._required"
        """
        msg = ''

        if not hasattr(self, '_required'):
            warnings.warn('List "self._required" not implemented. Will use an empty list!')
            self._required = []

        for a in self._required:
            if not a in self.params.keys():
                msg += '\n\t* required parameter "{}" not present'.format(a)
            elif self.params[a] is None and not tolerate_None:
                msg += '\n\t* required parameter "{}" must not be <None>'.format(a)

        if msg:
            msg = 'Error while checking for mandatory arguments' + msg
            raise ValueError(msg)
        else:
            return True


    # just a stub
    def submit(self):
        """write the submit file and submit the job"""
        raise NotImplementedError()


    # Some class properties // these all will fail if not initialized
    # SR: I must say that I do not see any reason to make these explicit
    # SR: properties here
    # SR: May be modified at some point
    @property
    def params(self):
        return self._params

    @property
    def setupcommands(self):
        """
        Additional variables for the job. For example the famous
        ``ulimit -s unlimited`` for FHIaims or any other things which need
        to be set before the actual job can start.
        """
        return self._setupcommands

    @property
    def environment(self):
        """
        List, add and remove environment variables to the submit script.

        Multiple values can be added for each variable, they will be
        concatenated with ":".

        Values that are already set are removed from the variable if they
        are set again.

        Parameters
        ----------
        env_tuple : tuple with:
            variable : str
                The environment variable to be set.
            value : str
                The value of the variable to be set.
        """
        return self._environment

    @property
    def precmd(self):
        """
        Add a command to the pre-command section.

        Parameters
        ----------
        cmd : str
            A command string (bash syntax) to be executed before the main
            run command of the job.
        """
        return self._precmd

    @property
    def cmd(self):
        """
        The main command for the job to be executed. Usually, this will be
        something like:
            mpirun.openmpi ...
        """
        return self._cmd

    @property
    def postcmd(self):
        """
        Add a command to the post-command section.

        Parameters
        ----------
        cmd : str
            A command string (bash syntax) to be executed after the main
            run command of the job.
        """
        return self._postcmd

    # Methods to write the files and submit the job (as well as consistency
    # checks

    def parse_defaultfile(self):
        """
        Look for a default file in home folder
        (~/.rtools/defaults/submitagent_agentname.ini) or the <cwd> and set all
        defaults defined there.

        For the default format see:
            https://docs.python.org/2/library/configparser.html

        Additionally, we have a tweak in here which allows to just specify
        key-value pairs without any sections, ie..

            >>> walltime : 01:00:00
            >>> program = myprog.exe

        Actually, so far we do not at all support sections. Yet, there may be
        scenarios where this may be benefitial (e.g. different setups available
        with a switch). The infrastructure is there...
        """
        home = os.environ["HOME"]
        defpath = os.path.join(home, ".rtools", "defaults")
        agent = self.__class__.__name__.lower()

        filepaths = [os.path.join(defpath, "submitagent_"+agent+".ini"),
                     os.path.join(os.getcwd(), "submitagent_"+agent+".ini")]

        for filepath in filepaths:
            if os.path.isfile(filepath):
                fdefaults = SafeConfigParser()
                # fake a header in case, see http://stackoverflow.com/a/2819788
                fdefaults.readfp(FakeSecHead(open(filepath)))
                if fdefaults.items('asection') or len(fdefaults.sections()) > 1:
                    print("Found default file ({0}), importing...".format(filepath))
                sections = fdefaults.sections()
                for section in sections:
                    defdict = dict(fdefaults.items(section))
                    for key, value in defdict.items():
                        if self._check_arg(key):
                            print("\t{} : {}".format(key, value))
                            self.defaults[key] = value


    def _expand_environment(self, var_key='export_variables'):
        """
        Expand the environment variables. Will fail, if <var_key> is
        not a key of the default-dict..
        """
        for key, val in self.params[var_key].items():
            # make sure we put quotation marks around the thing
            #if len(val.split()) > 1:
            val = '{}'.format(val.strip('"').strip("'"))
            self.environment.add(key.strip(), val)

    # some templates
    def _tp_environment(self):
        """Get additional environment variables for the job."""
        env_str = ""
        n_val = ""
        for key, value in self.environment.items():
            if len(value) > 1:
                for item in value:
                    # BUGFIX: item may be of type integer/float and this thing
                    # then fails
                    n_val = n_val + str(item) +":"
            else:
                n_val = value[0]
            env_str += '\nexport {key}="{value}"'.format(key=key, value=n_val)

        if not env_str:
            env_str = '# no user-defined environment variables'
        return env_str[1::]

    def _tp_precommand(self):
        """Get the command string for the pre-command section."""
        cmdstr = ""
        if len(self.precmd) != 0:
            for cmd in self.precmd:
                cmdstr += cmd + "\n"
        return cmdstr

    def _tp_program(self):
        """Get the binary of the main program (CASTEP, AIMS, LAMMPS, etc)."""
        prog = self.params.get("program")
        if not prog:
            raise RuntimeError('No "program" specified')
        return prog

    def _tp_command(self):
        """Get the command string for the main job command."""
        cmdstr = ""
        if len(self.cmd) != 0:
            for cmd in self.cmd:
                cmdstr += cmd + "\n"
        return cmdstr

    def _tp_postcommand(self):
        """Get the command string for the post-command section."""
        cmdstr = ""
        if len(self.postcmd) != 0:
            for cmd in self.postcmd:
                cmdstr += cmd + "\n"
        return cmdstr

    def _tp_walltime(self):
        """Get the walltime for the job"""
        walltime = self.params.get("walltime")

        #interpret as hours if only a number is given
        if isinstance(walltime, (int,float)):
            walltime = "{}:00:00".format(int(walltime))
        elif isinstance(walltime, str):
            try:
                h, m, s = walltime.split(':')
            except ValueError:
                warnings.warn('Passing walltime hours as string is deprecated')
                # this is a legacy feature:
                # if string cannot be split, also intepret it as hours
                walltime = '{}:00:00'.format(walltime)

        return walltime


# SR: what is the use of this functionality?
def get_defaults(agent, **required_arguments):
    """
    Collect default values from SubmitAgent class and default file and
    return them to be displayed.

    Parameters
    ----------
    agent : object or str
        The actual class or a string with the name of the class to test.
    required_arguments : key,value pairs
        All arguments required by the Agent (no optional arguments needed)

    Returns
    -------
    defaults : dict
        All defined defaults.
    """
    if isinstance(agent, str):
        mod_str = "rtools.submitagents.arthur.{}".format(agent.lower())
        module = importlib.import_module(mod_str)
        ag = getattr(module, agent.lower().capitalize())
        required_arguments["check_consistency"] = False
        required_arguments["dryrun"] = True
        try:
            with open(os.devnull, "w") as f:
                old_stdout = sys.stdout
                sys.stdout = f
                R = ag(**required_arguments)
                defaults = R.defaults
        finally:
            f.close()
            sys.stdout = old_stdout
    else:
        raise NotImplementedError("This function is not yet implemented\
for objects.")
    return defaults


# helper functionality for the walltime
def get_sec(time_str):
    """
    Split the walltime string to obtain seconds
    """
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)
