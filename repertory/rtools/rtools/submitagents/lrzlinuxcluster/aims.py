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

def submit(**kwargs):
    """Wrapper for legacy castep calculator support."""
    agent = Aims(**kwargs)
    return agent.submit()

class Aims(LinuxClusterAgent):
    """
    FHI-aims submit agent for the LRZ linux cluster.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = Aims(*args, **kwargs)
        >>> # this writes the jobfile and submits it to the batch loader
        >>> agent.submit()

    Initialization
    --------------
    ``program'' : string
        The aims binary *without* any mpi-related precommands.Note that you
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

    ``mpi_command'' : string, optional (default="mpiexec")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND. Make sure that this is not in conflict with the
        <job_type>!

    ``slurmname'' : string, optional (default=None)
        The name of the job for the batch loader. Defaults to the basename of
        <job_dir>. Note that the lenght is restricted to 10 characters, and the
        string will be cut at the end in case.

    ``job_dir'' : string, optional (default=${PWD})
        The directory containig the files for the job. Will be the working
        directory a.k.a. starting point on the node. Defaults to the current
        working directory.

    ``aims_outfile'' : string, optional (default=None)
        File to which the stdout of FHIaims is directed. Defaults to
        <job_name>.out

    ``outfile'' : string, optional (default=None)
        The outfile/errorfile to which all stdout is directed. Defaults to
        <job_dir>/<slurmname>.%j.%N.out.

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

    ``dependency'' : string (default=None)
        Submitting jobs with dependencies on other jobs. Only works if those
        jobs run on the same cluster.  You have to enter here all that follows
        the --dependency flag of sbatch.

        For details see:
            https://www.lrz.de/services/compute/linux-cluster/batch_parallel/specifications/#jobcontr
    ---
    Simon P. Rittmeyer (TUM), 2017
    """


    def __init__(self, **kwargs):
        # these will be additional/overwrite the parent's defaults
        self._defaults = {'mpi_command' : 'mpiexec',
                          'job_name' : 'aims',
                          'aims_outfile' : None,
                          'job_type' : 'MPICH'}

        super(Aims, self).__init__(**kwargs)

        # Set additional setup data for FHI-aims
        envs = {"OMP_NUM_THREADS": "1",
                "MKL_DYNAMIC": "FALSE",
                "MKL_NUM_THREADS": "1"}

        for item in envs.items():
            self.environment.add(*item)


        # well, this is FHIaims after all...
        self.precmd.add('ulimit -s unlimited')

        # this is just to properly run FHI-aims on supermuc
        self.cmd.add("$mpi_command $program > $aimsout")

        # steps to do all the setup
        self.aims_slurm_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def _check_input_sanity(self):
        # overload parent routine here
        if self.params['aims_outfile'] is None:
            self.params['aims_outfile'] = self.params['job_name'] + '.out'
        super(Aims, self)._check_input_sanity()


    def aims_slurm_template(self):
        self.slurm_dict["ENV"] = self.slurm_dict["ENV"] \
            + "\n# This one is to properly run MPI\n" \
            + r'mpi_command="{_TP_mpi_command}"' + "\n" \
            + "\n# redirecting FHI aims output\n" \
            + r"aimsout={_TP_aimsout}" + '\n'

    def _tp_aimsout(self):
        return self.params['aims_outfile']

    def _tp_mpi_command(self):
        return "{} -n {}".format(self.params.get("mpi_command"),
                                 self._tp_ncpu())

    def check_consistency(self):
        """check for input completeness"""
        program = self._tp_program()
        walltime_sec = get_sec(self._tp_walltime())

        # check if the program is executable
        if not which(program):
            # check all additional paths specified
            if all([which(program, path=str(path)) is None for path in self.environment.values()]):
                raise Warning('Cannot find <program> by invoking `which()`. If you did not do fancy bash aliasing, your job will crash!')

        control_path = os.path.join(self.params['job_dir'],"control.in")
        geometry_path = os.path.join(self.params['job_dir'],"geometry.in")

        if not os.path.exists(geometry_path):
            raise Warning('No geometry.in in <job_dir>. Your job will crash!')

        if not os.path.exists(control_path):
            raise Warning('No control.in in <job_dir>. Your job will crash!')
        else:
            # check for runtime flag
            with open(control_path, 'r') as controlfile:
                found = False
                for line in controlfile:
                    if 'walltime' in line.lower():
                        found = True
            if not found:
                with open(control_path, 'a') as controlfile:
                    # down-scale walltime limit to make sure that
                    # the job + ensuing IO can finish.
                    if walltime_sec < 24*60*60:
                        scale = .9
                    else:
                        scale = .95
                    controlfile.write(
                        '\nwalltime {} # added by submit script'.format(
                            int(walltime_sec*scale)))

