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
Module to submit [MDsim][1] runs to arthur.

[1]: https://gitlab.lrz.de/simonrittmeyer/MDsim
"""

from __future__ import print_function

from rtools.submitagents.arthur.pythonscript import PythonScriptAgent
from rtools.submitagents import get_sec


class SurfDiffAgent(PythonScriptAgent):
    def __init__(self, **kwargs):

        self.defaults = {'copyback' : ['*.py',
                                       '*.dat',
                                       '*.eta',
                                       '*.pot',
                                       '*.cfg',
                                       'output'],
                         'program' : 'SurfDiff',
                         'configfile' : None,
                         'cmd_args' : None,
                         'seed' : 'MDsim'}

        PythonScriptAgent.__init__(self, **kwargs)

        # creating the precommand
        if self.params['configfile'] is not None:
            self.params['configfile'] = 'configfile="-i {}"'.format(self.params['configfile'])
            self.precmd.add(self.params['configfile'])

        cmd_args = self.params['cmd_args']
        if cmd_args is None:
            flags = ''
        else:
            flags = ''
            for arg, val in cmd_args:
                if arg in ['io.seed',
                           'misc.walltime']:
                    continue
                flags +='--{}="{}" '.format(arg, val)

        flags += '--io.seed="{}" '.format(self.params['seed'])
        flags += '--misc.walltime="{}"'.format(walltime_sec = get_sec(self._tp_walltime()))

        self.precmd.add("flags='{}'".format(flags))

        # remove the old command first
        self.cmd.remove(-1)
        self.cmd.add('$python_bin $pyflags $program $configfile $flags')
