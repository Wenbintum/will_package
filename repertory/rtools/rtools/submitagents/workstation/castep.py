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

import os
from rtools.filesys import which
from rtools.submitagents.workstation import WorkstationAgent
from rtools.submitagents import get_sec

def submit(seed, **kwargs):
    """Wrapper for legacy castep calculator support."""
    R = Castep(seed=seed, **kwargs)
    R.submit()
    del R


class Castep(WorkstationAgent):
    """
    Castep submit agent.

    Class that automatically runs a (readily prepared) CASTEP job on the local
    workstations.

    The function writes a bash script, creates the results folder if not
    already existing and submits the job. There is now support to also copy
    selected files to an export directory instead of/additionally to the
    respective /data/${USER}/... path.

    Parameters
    ----------
    ``seed`` : string
        Seed for the CASTEP calculation.

    ``pp_dir`` : string, optional (default=None)
        Path to the pseudopotentials, will be exported as PSPOT_DIR.

    ``mpi_command`` : string, optional (default="mpirun.local")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND.
    ---
    Simon P. Rittmeyer (TUM), 2016
    """


    def __init__(self, **kwargs):
        self.__doc__ += "\n" + WorkstationAgent.__init__.__doc__

        # these will be additional/overwrite the parent's defaults
        self.defaults = {'mpi_command' : 'mpirun.local',
                         'pp_dir' : None,
                         'seed' : None,
                         'copyback' : ['*.cell',
                                       '*.param',
                                       '*.castep',
                                       '*.bands',
                                       '*.geom',
                                       '*.err']
                         }

        self.required = ['seed']

        super(Castep, self).__init__(**kwargs)

        # Set additional setup data for CASTEP
        self.environment.add("OMP_NUM_THREADS", 1)
        self.environment.add("PSPOT_DIR", self.params["pp_dir"])

        # this is for binary compatibility after upgrade to jessie
        self.cmd.add("$mpi_command -np $nproc $program $seed")

        # default to <job_dir>/results for the results dir as before
        self.params.update({'result_dir' : kwargs.get('result_dir', 'results')})

        # steps to do all the setup
        self.castep_bash_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def _check_input_sanity(self):
        # just check for a proper job name here
        if self.params['jobname'] is None:
            self.params['jobname'] = self.params['seed']
        super(Castep, self)._check_input_sanity()

    def castep_bash_template(self):
        self.bash_dict["ENV"] = self.bash_dict["ENV"] \
            + r"mpi_command={_TP_mpi_command}" + "\n" \
            + "\n" + r"seed={_TP_SEED}"+"\n"

    def _tp_seed(self):
        return self.params['seed']

    def _tp_mpi_command(self):
        return self.params.get("mpi_command")

    def check_consistency(self):
        """check for input completeness"""
        program = self._tp_program()
        # check if the program is executable
        if not which(program):
            # check all additional paths specified
            if all([which(program, path=str(path)) is None for path in self.environment.values()]):
                raise Warning('Cannot find <program> by invoking `which()`. If you did not do fancy bash aliasing, your job will crash!')

        seed = self.params['seed']
        cellfile_path = os.path.join(self.params['job_dir'], seed + '.cell')
        if not os.path.exists(cellfile_path):
            raise Warning('No cellfile in <job_dir>. Your job will crash!')

        paramfile_path = os.path.join(self.params['job_dir'], seed + '.param')
        if not os.path.exists(paramfile_path):
            raise Warning('No paramfile in <job_dir>. Your job will crash!')
