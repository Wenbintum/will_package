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
from rtools.submitagents import get_sec
from rtools.submitagents.lrzlinuxcluster import LinuxClusterAgent


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

class Castep(LinuxClusterAgent):
    """
    Castep submit agent for the SLURM batch loader on the LRZ Linux Cluster.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = Castep(*args, **kwargs)
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

    ``clusters'' : string ({"mpp1", *"mpp2"*})
        The clusters this job shall be submitted to. Clusters differ in node
        architecture and in available memory and CPU per node. More details can
        be found here:

            https://www.lrz.de/services/compute/linux-cluster/batch_parallel/specifications/#parenvs

        Note that you cannot necessarily submit to each cluster from each login
        node.

    ``nnodes'' : integer
        The number of requested nodes. The actual number of available CPU and
        memory depends on the cluster you submit to.

    ``email_address'' : string
        Your mail address to which notifications are sent. This is a
        requirement on LRZ systems.

    ``pp_dir'' : string, optional (default=None)
        Path to the pseudopotentials, will be exported as PSPOT_DIR.

    ``slurmname'' : string, optional (default=None)
        The name of the job for the batch loader. Defaults to the basename of
        <job_dir>. Note that the lenght is restricted to 10 characters, and the
        string will be cut at the end in case.

    ``job_dir'' : string, optional (default=${PWD})
        The directory containig the files for the job. Will be the working
        directory a.k.a. starting point on the node. Defaults to the current
        working directory.

    ``outfile'' : string, optional (default=None)
        The outfile to which all stdout/stderr is directed. Defaults to
        <job_dir>/<slurmname>.%j.%N.out.

    ``export variables'' : dict, optional (default = {})
        Environment variables that will be exported before calling the program.
        For instance
            >>> export_variables = {'PYTHONPATH' : <my_python_path>}
        Take care of spelling and do include full paths in any case.

    ``mpi_command'' : string, optional (default="mpiexec")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND.

    ``unload_modules'': list of strings, optional (default=[])
        List of modules that is unloaded before any new modules are loaded.

    ``load_modules'' : list of strings, optional (default=[])
        List of modules that is loaded before any program is executed.

    ``dryrun'' : boolean, optional (default=True)
        If <dryrun> = True then the jobfile is written but *NOT* submitted.

    ``check_consistency'' : boolean, optional (default=True):
        Check consistency of the created and available input, if this
        functionality is implemented by the derived subclass.

    ``dependency'' : string (default=None)
        Submitting jobs with dependencies on other jobs. Only works if those
        jobs run on the same cluster.  You have to enter here all that follows
        the --dependency flag of sbatch.

        For details see:
            https://www.lrz.de/services/compute/linux-cluster/batch_parallel/specifications/#jobcontr

    ---
    Simon P. Rittmeyer (TUM), 2016
    """


    def __init__(self, **kwargs):
        self.__doc__ += "\n" + LinuxClusterAgent.__init__.__doc__

        # these will be additional/overwrite the parent's defaults
        self._defaults = {'mpi_command' : 'mpiexec',
                          'pp_dir' : None,
                          'seed' : None}

        self._required = ['seed']

        modules = kwargs.pop('load_modules', [])
        unload_modules = kwargs.pop('unload_modules', [])

        # mpi intel is most basic...
        if not ('mpi.intel' in modules or 'mpi.intel' in unload_modules):
            modules.append('mpi.intel')

        kwargs['unload_modules'] = unload_modules
        kwargs['load_modules'] = modules

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
        self.castep_slurm_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def _check_input_sanity(self):
        # overload parent routine here
        if self.params['slurmname'] is None:
            self.params['slurmname'] = self.params['seed']
        super(Castep, self)._check_input_sanity()

    def castep_slurm_template(self):
        self.slurm_dict["ENV"] = self.slurm_dict["ENV"] \
            + "\n# This one is to properly run MPI\n" \
            + r"mpi_command={_TP_mpi_command}" + "\n" \
            + "\n# The castep seed\n" + r"seed={_TP_SEED}"+"\n\n"

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
