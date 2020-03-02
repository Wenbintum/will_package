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
from __future__ import print_function

from rtools.filesys import which
from rtools.submitagents.arthur.castep import Castep


def submit(seed, **kwargs):
    """Wrapper for legacy castep calculator support."""
    R = CastepPostProc(seed=seed, **kwargs)
    R.submit()
    del R


class CastepPostProc(Castep):
    """
    Castep submit agent.

    Class that automatically submits a (readily prepared) CASTEP job to the
    local cluster (arthur) and runs a post processing calculation afterwards.

    The main difference to the parent class is the addition of a post-command
    section, with a bit of python magic.

    The function writes a PBS script, creates the results folder if not
    already existing and submits the job. There is now support to also copy
    selected files to an export directory instead of/additionally to the
    respective /data/${USER}/... path.

    Parameters
    ----------
    ``seed`` : string
        Seed for the CASTEP calculation.

    ``pp_dir`` : string
        Path to the pseudopotentials, will be exported as PSPOT_DIR.

    ``postprogram`` : string
        Path to the postprocessing executable. Will be exported as POSTPROGRAMM.

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
        self.defaults = {'postprogram' : None}
        self.required = ['postprogram']

        Castep.__init__(self, **kwargs)
        self.check_postproc()

        # add the postprogram to the environment
        self.casteppostproc_pbs_template()

        self.prepare_continuation()

    def casteppostproc_pbs_template(self):
        self.pbs_dict["ENV"] = self.pbs_dict["ENV"] \
            + "\n" + r"# This run includes post processing" + "\n" + r"postprogram={_TP_POSTPROGRAM}"+"\n\n"

    def check_postproc(self):
        """check for input completeness"""
        # additionally check for the postprogram
        postprogram = self._tp_postprogram()
        # check if the program is executable
        if not which(postprogram):
            # check all additional paths specified
            if all([which(postprogram, path=str(path)) is None for path in self.environment.values()]):
                raise Warning('Cannot find <postprogram> by invoking `which()`. If you did not do fancy bash aliasing, your job will crash!')


    def _tp_postprogram(self):
        """Get the binary of the main program (CASTEP, AIMS, LAMMPS, etc)."""
        postprog = self.params.get("postprogram")
        if not postprog:
            raise RuntimeError('No "post-program" specified. Use plain CASTEP calculator!')
        return postprog


    def prepare_continuation(self):
        self._postcmd = """
# save the scf files
cp ${seed}.param ${seed}.param.scf
cp ${seed}.castep ${seed}.castep.scf

# append the continuation line to the param file
paramfile="${seed}.param"
echo "" >> $paramfile
echo "continuation : $(seed).check" >> $paramfile

# mpi parallelism for castep tools is buggy
# this has changed due to the jessie update of arthur
$postprogram $seed

# restore the original scf output files
mv ${seed}.param ${seed}.param.continuation
mv ${seed}.castep ${seed}.castep.continuation
mv ${seed}.param.scf ${seed}.param
mv ${seed}.castep.scf ${seed}.castep
""".split("\n")
