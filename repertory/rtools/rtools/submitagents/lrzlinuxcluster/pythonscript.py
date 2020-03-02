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
Module to submit python scripts to the lrz linux cluster.
"""

from __future__ import print_function
import os

from rtools.submitagents.lrzlinuxcluster import LinuxClusterAgent


def submit(*args, **kwargs):
    agent = PythonScriptAgent(*args, **kwargs)
    return agent.submit()

class PythonScriptAgent(LinuxClusterAgent):
    """
    Class to submit python script jobs to the SLURM batch loader on the LRZ
    Linux Cluster. Very similar to the arthur submit agent, but implemented
    more recently.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = PythonScriptAgent(*args, **kwargs)
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

    ``pythonpath'' : string, optional (default=None)
        Pythonpath to be exported. If <None> the current ${PYTHONPATH} value
        will be used.

    ``python_flags'' : string, optional (default=None)
        Flags for the python interpreter, *NOT* the python script.

    ``pyscript_flags'' : string, optional (default=None)
        Flags for the pyscript, *NOT* the python interpreter.

    ``python_module'' : string, optional (default="python/2.7_anaconda_nompi")
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
    ---
    Simon P. Rittmeyer (TUM), 2016
    """
    def __init__(self,
                 pyscript,
                 pyscript_flags='',
                 pythonpath=None,
                 python_flags='',
                 python_module='python/2.7_anaconda_nompi',
                 **kwargs):

        kwargs['program'] = pyscript
        # make sure that we first unload python

        modules = kwargs.pop('load_modules', [])
        unload_modules = kwargs.pop('unload_modules', [])
        modules.append(python_module)
        unload_modules.append('python')
        if 'python/2.7_anaconda_mpi' == python_module:
            for m in modules:
                if 'mpi.intel' in m:
                    raise ValueError('Cannot combine `python/2.7_anaconda_mpi` with `mpi.intel`')
        if not 'mpi.intel' in modules:
            unload_modules.append('mpi.intel')
        kwargs['unload_modules'] = unload_modules
        kwargs['load_modules'] = modules

        # add the python path to the environment variables
        export_variables = kwargs.pop('export_variables', {})
        if not 'PYTHONPATH' in export_variables.keys():
            if pythonpath is None:
                pythonpath = os.environ.get('PYTHONPATH')
                if pythonpath.endswith(':'):
                    pythonpath = pythonpath[:-1]
            if pythonpath is not None:
                export_variables["PYTHONPATH"]= '"{}:${{PYTHONPATH}}"'.format(pythonpath)

        export_variables["python_flags"] = python_flags
        export_variables["pyscript_flags"] = pyscript_flags

        kwargs['export_variables'] = export_variables

        super(PythonScriptAgent, self).__init__(**kwargs)

        # remove the old command
        self.cmd.add('python $python_flags $program $pyscript_flags')

