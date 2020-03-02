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
from rtools.submitagents.arthur import ArthurAgent


def submit(**kwargs):
    """Wrapper for legacy castep calculator support."""
    R = Aims(**kwargs)
    R.submit()
    del R


class Aims(ArthurAgent):
    """
    Aims submit agent.

    Class that automatically submits a (readily prepared) FHIaims job to the
    local cluster (arthur).

    The function writes a PBS script, creates the results folder if not
    already existing and submits the job. There is now support to also copy
    selected files to an export directory instead of/additionally to the
    respective /data/${USER}/... path.

    Initialization
    --------------
    ``job_dir`` : string
        Jobfolder where all the prepared input is in. Default is the
        current working directory.

    ``program`` : string
        Complete path to the binary that is to be executed.

    ``result_dir`` : string
        Folder where the output specified by `copyback` is copied back from
        the tick node(s). By default this will be job_dir/results

    ``pbsname`` : string
        Name associated with the job in the PBS system. By default it will
        be the parent folder's name.

    ``walltime`` : integer (default = 10), or string in format `hh:mm:ss`
        Walltime. If an integer is passed, it will be interpreted as hours,
        more control is provided through explicit strings passed.

    ``aims_outfile'' : string, optional (default=None)
        File to which the stdout of FHIaims is directed. Defaults to
        <job_name>.out

    ``mpi_command'' : string, optional (default="mpiexec")
        Command to call the suitable MPI machinery. Will be exported as
        MPI_COMMAND. Make sure that this is not in conflict with the

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

    ``copy`` : List of strings (default = ['*'])
        Files that are supposed to be copied on the tick node.  Symlinks
        will be resolved.

    ``copyback`` : List of strings (default = ['*'])
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
        Check for input consistency (if *.in files exist).
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
    """

    def __init__(self, **kwargs):
        self.defaults = {'mpi_command' : 'mpiexec',
                          'job_name' : 'aims',
                          'aims_outfile' : None,
                         }

        super(Aims, self).__init__(**kwargs)

        # well, this is FHIaims after all...
        self.precmd.add('ulimit -s unlimited')

        # this is just to properly run FHI-aims on supermuc
        self.cmd.add("$mpi_command $program > $aimsout")

        # all-time-favourites:
        envs = {"OMP_NUM_THREADS": "1",
                "MKL_DYNAMIC": "FALSE",
                "MKL_NUM_THREADS": "1",
                "LD_LIBRARY_PATH" : "${LD_LIBRARY_PATH}:/usr/local/stow/Intel_Composer/share/intel/composer_xe_2013_sp1.1.106/mkl/lib/intel64",
                }

        for item in envs.items():
            self.environment.add(*item)

        # steps to do all the setup
        self.aims_pbs_template()
        if self.params["check_consistency"]:
            self.check_consistency()

    def aims_pbs_template(self):
        self.pbs_dict["ENV"] = self.pbs_dict["ENV"] \
            + "\n# This one is to properly run MPI\n" \
            + r'mpi_command="{_TP_mpi_command}"' + "\n" \
            + "\n# redirecting FHI aims output\n" \
            + r"aimsout={_TP_aimsout}"+"\n\n"

    def _tp_aimsout(self):
        return self.params['aims_outfile']

    def _tp_mpi_command(self):
        return "{} --hostfile ${{PBS_NODEFILE}}".format(self.params.get("mpi_command"))

    def check_consistency(self):
        """check for input completeness"""
        if self.params['aims_outfile'] is None:
            self.params['aims_outfile'] = self.params['job_name'] + '.out'

        # make sure that we copy back the outfile
        if not self.params['aims_outfile'] in self.params['copyback']:
            self.params['copyback'] += [self.params['aims_outfile']]

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

