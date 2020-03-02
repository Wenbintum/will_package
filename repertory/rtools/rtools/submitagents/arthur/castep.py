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
from rtools.submitagents.arthur import ArthurAgent
from rtools.submitagents import get_sec

def submit(seed, **kwargs):
    """Wrapper for legacy castep calculator support."""
    R = Castep(seed=seed, **kwargs)
    R.submit()
    del R


class Castep(ArthurAgent):
    """
    Castep submit agent.

    Class that automatically submits a (readily prepared) CASTEP job to the
    local cluster (arthur).

    The function writes a PBS script, creates the results folder if not
    already existing and submits the job. There is now support to also copy
    selected files to an export directory instead of/additionally to the
    respective /data/${USER}/... path.

    Parameters
    ----------
    ``seed`` : string
        Seed for the CASTEP calculation.

    ``job_dir`` : string
        Jobfolder where all the prepared input is in. Default is the
        current working directory.

    ``pp_dir`` : string, optional (default=None)
        Path to the pseudopotentials, will be exported as PSPOT_DIR.

    ``result_dir`` : string
        Folder where the output specified by `copyback` is copied back from
        the tick node(s). By default this will be job_dir/results

    ``mpi_command`` : string, optional (default="mpirun")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND.

    ``pbsname`` : string
        Name associated with the job in the PBS system. By default it will
        be the parent folder's name.

    ``walltime`` : integer (default = 10), or string in format `hh:mm:ss`
        Walltime. If an integer is passed, it will be interpreted as hours,
        more control is provided through explicit strings passed.

    ``ncpu`` : integer (default = 8)
        Number of cores requested. Currently there is no support for more
        than one node. But this can be changed easily in the jobfilestring.

    ``memory`` : string (default = '1gb')
        Requested memory per core. Note that we require an actual quantity
        specifier, ie., a number is not enough.

    ``node_features`` : string or list of strings (default = [])
        Additional features of the requested nodes like ie. the operating
        system or architecture.
        Currently available:
            * 'Intel'
            * 'AMD'
            * 'jessie'
            * 'Opteron6272'
            * 'Opteron2435'
            * 'Opteron6172'
            * 'XeonE5640'
            * 'XeonE5540'
            * 'em64t'
            * 'amd64'
            * 'x86_64'
            * 'opteron'
            * 'xeon'
            * 'smp'
        Any other option will be disregarded.

    ``exclude_nodes`` : string or list of strings (default = [])
        Nodes on which the job should not run due to known issues.

    ``copy`` : List of strings (default = ['*.param', '*.cell'])
        Files that are supposed to be copied on the tick node.  Symlinks
        will be resolved.

    ``copyback`` : List of strings (default = ['*.cell', '*.param',
                                                '*.castep', '*.err',
                                                '*.geom', '*.bands'])
        Files that are copied back to `result_folder`. Wildcards are
        supported.

    ``export_dir`` : string (default = None)
        Folder where the output specified by `copy_to_export` is copied back
        from the tick node(s). Use this option if you have large output
        files as e.g. *.check files that otherwise could violate your quota
        on /data/${USER} rather rapidly... Note that files can be copied to
        `result_dir` *and* `export_dir`.
        By default `export_dir` evaluates to
            ``/net/${HOST}/${USER}/${`job_dir`#$/data/${USER}}``
        (bash notation) if not given but necessary, ie. if `copyback_export`
        is not the empty string.

    ``copyback_export`` : List of strings (default = [''])
        Files that are copied back to the export path given by `export_dir`.
        Wildcards are supported.

    ``email`` : Boolean (default = True)
        Send email notifications upon job exit and abort.

    ``email_address'' : string (default=None)
        Specify the email adress. Defaults to
        <user>@theo.chemie.tu-muenchen.de. If a value is passed here,
        <email> = True automatically.

    ``check_consistency`` : Boolean (default = True)
        ...CASTEP/AIMS only...
        Check for input consistency (if *.cell and *.param file exist).
        Additionally, adds the RUM_TIME flag with the appropriate walltime
        specified to the *.param file if not already specified.

    ``debug`` : Boolean (default = False)
        Print each executed command and full environment to PBS outfile.

    ``cleanup`` : Boolean (default = False)
        Delete temporary folder from the tick after all requested files
        have been copied back successfully.

    ``infofile`` : str (default = "arthur.info")
        The file which will contain information such as the PBS job id, the
        nodes on which your job actually runs and the local working
        directory on these nodes.

    ``dryrun`` : boolean (Default = False)
        If True, job will not be submitted, ie. the qsub command is
        omitted. Automatically set False if `return_id` is True.
    ---
    Simon P. Rittmeyer (TUM), 2016
    """


    def __init__(self, **kwargs):
        # these will be additional/overwrite the parent's defaults
        self.defaults = {'mpi_command' : 'mpirun',
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
        if self.params.get('mpi_command') == 'mpirun.local.oldstable':
            self.cmd.add("$mpi_command --hostfile $PBS_NODEFILE $program $seed")
        else:
            self.cmd.add("$mpi_command -n $PBS_NP $program $seed")

        # default to <job_dir>/results for the results dir as before
        self.params.update({'result_dir' : kwargs.get('result_dir', 'results')})

        # steps to do all the setup
        self.castep_pbs_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def _check_input_sanity(self):
        # just check for a proper pbs name here
        if self.params['pbsname'] is None:
            self.params['pbsname'] = self.params['seed']
        super(Castep, self)._check_input_sanity()

    def castep_pbs_template(self):
        self.pbs_dict["ENV"] = self.pbs_dict["ENV"] \
            + "\n# This one is new since the cluster jessie update\n" \
            + r"mpi_command={_TP_mpi_command}"\
            + "\n\n" + r"seed={_TP_SEED}"+"\n"

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
