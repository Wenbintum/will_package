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
import warnings
from rtools.filesys import which
from rtools.submitagents import get_sec
from rtools.submitagents.supermuc import SuperMucAgent


def submit(seed, **kwargs):
    """Wrapper for legacy castep calculator support."""
    if not 'pp_dir' in kwargs.keys():
        try:
            pp_dir = os.environ['PSPOT_DIR']
        except KeyError:
            pass
            # going to fail anyway

    agent = Castep(seed=seed, **kwargs)
    return agent.submit()

class Castep(SuperMucAgent):
    """
    Castep submit agent for the SuperMuc.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = Casteo(*args, **kwargs)
        >>> # this writes the jobfile and submits it to the batch loader
        >>> agent.submit()

    Initialization
    --------------
    ``seed'' : string
        Seed for the CASTEP calculation.

    ``program'' : string
        The castep binary *without* any mpi-related precommands.Note that you
        either have to provide a full path, or that you have to export
        corresponding variables (see ``export_variables''). The SLURM shell
        does *NOT* inherit any paths you have set in the calling shell.

    ``walltime'' : string or integer
        The required walltime. Either a string in format "hh:mm:ss" or an
        integer which will then be interpreted as hours.

    ``email_address'' : string
        Your mail address to which notifications are sent. This is a
        requirement on LRZ systems.


    ``architecture'' : string ({"fat", "thin", *"phase2"*})
        The node-architecture this job shall be submitted to. Clusters differ in node
        architecture and in available memory and CPU per node. More details can
        be found here:

            https://www.lrz.de/services/compute/supermuc/loadleveler/

        Note that you cannot necessarily submit to each cluster from each login
        node.

    ``job_class'' : string
        Job class. Depends on the node architecture you choose.
            'thin' : ['test', 'general', 'large']
            'fat' : ['fattest', 'fatter', 'fat']
            'phase2' : ['test', 'micro', 'general', 'big']
        More details here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#jobclass

    ``nnodes'' : integer
        The number of requested nodes. The actual number of available CPU and
        memory depends on the cluster you submit to.

    ``ntasks'' : integer, optional (default=None)
        The total number of requested tasks, ie., processes. Cannot be combined
        with ntasks_per_node. If <None>, it will be max node cpu * nnodes
        See also here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#TOC

    ``ntasks_per_node'' : integer, optional (default=None)
        The number of requested tasks, ie., processes per node. Cannot be
        combined with ntasks. If <None> it will be max node cpu.
        See also here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#TOC

    ``island_count'' : list of two integer [min, max] (default = None)
        If you require more than one island (512 nodes!), specify here the
        minimum and maximum island count.

    ``pp_dir'' : string, optional (default=None)
        Path to the pseudopotentials, will be exported as PSPOT_DIR.

    ``mpi_command'' : string, optional (default="mpiexec")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND.

    ``job_dir'' : string, optional (default=${PWD})
        The directory containig the files for the job. Will be the working
        directory a.k.a. starting point on the node. Defaults to the current
        working directory.

    ``job_type'' : string, optional ({'parallel', *MPICH*'})
        Specifyer for parallel jobs parallelism. "parallel" for IBM mpi,
        "MPICH" for intel mpi.

    ``outfile'' : string, optional (default=None)
        The outfile to which all stdout/stderr is directed. Defaults to
        <job_dir>/<job_name>.%j.%N.out.

    ``errorfile'' : string, optional (default=None)
        The outfile to which all stdout/stderr is directed. Defaults to
        <job_dir>/<job_name>.$(schedd_host).$(jobid).err.

    ``export variables'' : dict, optional (default = {})
        Environment variables that will be exported before calling the program.
        For instance
            >>> export_variables = {'PYTHONPATH' : <my_python_path>}
        Take care of spelling and do include full paths in any case.

    ``unload_modules'': list of strings, optional (default=[])
        List of modules that is unloaded before any new modules are loaded.

    ``load_modules'' : list of strings, optional (default=[])
        List of modules that is loaded before any program is executed.

    ``dryrun'' : boolean, optional (default=True)
        If <dryrun> = True then the jobfile is written but *NOT* submitted.

    ``check_consistency'' : boolean, optional (default=True):
        Check consistency of the created and available input, if this
        functionality is implemented by the derived subclass.

    ``energy_policy_tag'' :  string, optional (default=None)
        The energy policy tag. For details see
            https://www.lrz.de/services/compute/supermuc/loadleveler/#energy
    ---
    Simon P. Rittmeyer (TUM), 2017
    """


    def __init__(self, **kwargs):
        self.__doc__ += "\n" + SuperMucAgent.__init__.__doc__

        # these will be additional/overwrite the parent's defaults
        self._defaults = {'mpi_command' : 'mpiexec',
                          'pp_dir' : None,
                          'seed' : None}

        self._required = ['seed']

        super(Castep, self).__init__(**kwargs)

        # Set additional setup data for CASTEP
        self.environment.add("OMP_NUM_THREADS", 1)

        if not self.params['pp_dir'] is None:
            self.environment.add("PSPOT_DIR", self.params["pp_dir"])
        else:
            warnings.warn("No ${PSPOT_DIR} exported")

        # this is just to properly run castep on the LRZ cluster
        self.cmd.add("$mpi_command $program $seed")

        # steps to do all the setup
        self.castep_loadleveler_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def _check_input_sanity(self):
        # overload parent routine here
        if self.params['job_name'] is None:
            self.params['job_name'] = self.params['seed']
        super(Castep, self)._check_input_sanity()

    def castep_loadleveler_template(self):
        self.loadleveler_dict["ENV"] = self.loadleveler_dict["ENV"] \
            + "\n# The castep seed\n" + r"seed={_TP_SEED}"+"\n\n"

    def _tp_seed(self):
        return self.params['seed']

    def check_consistency(self):
        """check for input completeness"""
        program = self._tp_program()
        # check if the program is executable
        if not which(program):
            # check all additional paths specified
            if all([which(program, path=str(path)) is None for path in self.environment.values()]):
                raise Warning('Cannot find <program> by invoking `which()`. If you did not do fancy bash aliasing, your job will crash!')

        walltime_sec = get_sec(self._tp_walltime())
        seed = self.params['seed']
        cellfile_path = os.path.join(self.params['job_dir'], seed + '.cell')
        if not os.path.exists(cellfile_path):
            raise Warning('No cellfile in <job_dir>. Your job will crash!')

        paramfile_path = os.path.join(self.params['job_dir'], seed + '.param')
        if not os.path.exists(paramfile_path):
            raise Warning('No paramfile in <job_dir>. Your job will crash!')
        else:
            # check for runtime flag
            with open(paramfile_path, 'r') as paramfile:
                found = False
                for line in paramfile:
                    if 'run_time' in line.lower():
                        found = True
            if not found:
                with open(paramfile_path, 'a') as paramfile:
                    # down-scale walltime limit to make sure that
                    # the job + ensuing IO can finish.
                    if walltime_sec < 24*60*60:
                        scale = .9
                    else:
                        scale = .95
                    paramfile.write(
                        '\nRUN_TIME : {} # added by submit script'.format(
                            int(walltime_sec*scale)))
