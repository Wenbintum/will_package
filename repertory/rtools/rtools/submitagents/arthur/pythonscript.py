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
Module to python scripts to arthur.
"""

from __future__ import print_function
import os

from rtools.submitagents.arthur import ArthurAgent

def submit(*args, **kwargs):
    agent = PythonScriptAgent(*args, **kwargs)
    agent.submit()

class PythonScriptAgent(ArthurAgent):
    """
    Class to submit python script jobs to arthur.

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

    ``job_dir`` : string
        Jobfolder where all the prepared input is in. Default is the
        current working directory.

    ``result_dir`` : string
        Folder where the output specified by `copyback` is copied back from
        the tick node(s). By default this will be job_dir/results

    ``pbsname`` : string
        Name associated with the job in the PBS system. By default it will
        be the parent folder's name.

    ``python_cmd'' : string, optional (default = 'python27')
        The full command to call python.

    ``pythonpath'' : string, optional (default=None)
        Pythonpath to be exported. If <None> the current ${PYTHONPATH} value
        will be used.

    ``python_flags'' : string, optional (default=None)
        Flags for the python interpreter, *NOT* the python script.

    ``pyscript_flags'' : string, optional (default=None)
        Flags for the pyscript, *NOT* the python interpreter.

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
    """
    def __init__(self,
                 pyscript,
                 pyscript_flags='',
                 pythonpath=None,
                 python_flags='',
                 python_cmd='python2.7',
                 **kwargs):

        self.defaults ={'copyback' : ['*.py',
                                      '*.dat'],
                        'copy' : ['*.py'],
                        'ncpu' : 1
                        }


        kwargs['program'] = pyscript

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

        self.environment.add('python_bin', '"{}"'.format(python_cmd))

        # in case we run some aims somewhere...
        self.precmd.add('ulimit -s unlimited')

        # remove the old command
        self.cmd.add('$python_bin $python_flags $program $pyscript_flags')
