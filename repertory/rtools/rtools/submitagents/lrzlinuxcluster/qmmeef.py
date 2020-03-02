"""
Module to submit QM/Me+EF[1] runs to the LRZ linux cluster

[1]: https://gitlab.lrz.de/simonrittmeyer/MDsim
"""

from __future__ import print_function
import os

from rtools.submitagents.lrzlinuxcluster.pythonscript import PythonScriptAgent
from rtools.submitagents.lrzlinuxcluster import resolve_home_work_vars

def submit(*args, **kwargs):
    agent = QMMeEFAgent(*args, **kwargs)
    return agent.submit()

class QMMeEFAgent(PythonScriptAgent):
    """
    Class to submit QMMe+EF[1] script jobs to the SLURM batch loader on the LRZ
    Linux Cluster. Very similar to the arthur submit agent, but implemented
    more recently.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = QMMeEFAgent(*args, **kwargs)
        >>> # this writes the jobfile and submits it to the batch loader
        >>> agent.submit()

    Initialization
    --------------
    ``pyscript'' : string
        Python script. Note that you either have to provide a full
        path, or that you have to export corresponding variables (see
        ``export_variables''). The SLURM shell does *NOT* inherit any paths you
        have set in the calling shell.

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

    ``castep_command'' : string
        The path to the CASTEP executable. Must be passed if not contained in
        "export_variables" as "CASTEP_COMMAND" or active user space.

    ``castep2cube_command'' : string
        The path to the CASTEP2cube executable. Must be passed if not contained in
        "export_variables" as "CASTEP2CUBE_COMMAND" or active user space.

    ``castep_hirshfeld_command'' : string
        The path to the castep_Hirshfeld[2] executable. Must be passed if not contained in
        "export_variables" as "CASTEP_HIRSHFELD_COMMAND" or active user space.

    ``castep_pp_path'' : string
        The path to the CASTEP pseudopotentials. Must be passed if not
        contained in "export_variables" as "PSPOT_DIR" or active user space.

    ``lammps_command'' : string
        The path to the lammps executable. Must be passed if not contained in
        "export_variables" as "LAMMPS_COMMAND" or active user space.

    ``pythonpath'' : string, optional (default=None)
        Pythonpath to be exported. If <None> the current ${PYTHONPATH} value
        will be used.

    ``python_flags'' : string, optional (default=None)
        Flags for the python interpreter, *NOT* the python script.

    ``pyscript_flags'' : string, optional (default=None)
        Flags for the pyscript, *NOT* the python interpreter.

    ``python_module'' : string, optional (default="python2.7/anaconda_nompi")
        Python module to be used. You may use the "unload_modules" argument to
        unload the current environment first.

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


    [1]: https://gitlab.lrz.de/simonrittmeyer/MDsim
    [2]: https://gitlab.lrz.de/simonrittmeyer/castep_Hirshfeldv2.git
    ---
    Simon P. Rittmeyer (TUM), 2016
    """

    def __init__(self, *args, **kwargs):

        # add the python path to the environment variables
        export_variables = kwargs.pop('export_variables', {})

        for argname, exportname in [('castep_pp_path', 'PSPOT_DIR'),
                                    ('castep_command', 'CASTEP_COMMAND'),
                                    ('castep2cube_command', 'CASTEP2CUBE_COMMAND'),
                                    ('castep_hirshfeld_command', 'CASTEP_HIRSHFELD_COMMAND'),
                                    ('lammps_command' , 'LAMMPS_COMMAND')]:

            arg = kwargs.pop(argname, None)

            if arg is not None:
                export_variables[exportname] = '"{}"'.format(resolve_home_work_vars(arg.strip('"')))
            elif exportname in export_variables.keys():
                pass
            # try to fetch from user config
            elif argname not in export_variables.keys():
                arg = os.environ.get(exportname, None)
                if arg is None:
                    msg = 'Conditional argument "{}" neither direclty passed, nor contained in "export_variables" as "{}", nor available through active user environment'.format(argname, exportname)
                    raise ValueError(msg)
                else:
                    if arg.endswith(':'):
                        arg = arg[:-1]

                    export_variables[exportname] = '"{}"'.format(resolve_home_work_vars(arg.strip('"')))

        kwargs['export_variables'] = export_variables

        super(QMMeEFAgent, self).__init__(*args, **kwargs)
