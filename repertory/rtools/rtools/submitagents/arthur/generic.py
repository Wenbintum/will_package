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

from rtools.submitagents.arthur import ArthurAgent


class Generic(ArthurAgent):
    """
    The Generic agent allows any command to be used for the PBS job.
    This could be used when calling Python scripts which do
    AIMS or CASTEP calculations.
    """
    def __init__(self, cmd, **kwargs):
        """
        Parameters
        ----------
        cmd : str
            The actual command to be executed on the cluster.
        """
        super(Generic, self).__init__(**kwargs)

        self.setupcommands.add("ulimit -s unlimited")
        self.setupcommands.add(
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/stow/\
Intel_Composer/share/intel/composer_xe_2013_sp1.1.106/mkl/lib/intel64")
        envs = {"OMP_NUM_THREADS": "1",
                "MKL_DYNAMIC": "FALSE",
                "MKL_NUM_THREADS": "1"}

        for item in envs.items():
            self.environment.add(*item)

        self.cmd.add(cmd)
