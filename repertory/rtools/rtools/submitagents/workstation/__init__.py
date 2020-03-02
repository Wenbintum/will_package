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

import argparse
import importlib
import os
import glob
import subprocess
import time
import re
import sys
from collections import OrderedDict
from string import Formatter

from rtools.misc import get_close_matches
from rtools.misc import format_timing

from rtools.submitagents import Agent

class WorkstationAgent(Agent):
    """Base-class for all submitagents for different codes/tasks.

    An agent is supposed to handle the task of creating and
    running a bash file analoguous (as far as possible) to a PBS file

    ---
    Simon P. Rittmeyer (TUM), 2016.
    """

    def __init__(self, **kwargs):
        """
        Parameters
        ----------
        ``job_dir`` : string
            Jobfolder where all the prepared input is in. Default is the
            current working directory.

        ``program`` : string
            Complete path to the binary that is to be executed.

        ``result_dir`` : string
            Folder where the output specified by `copyback` is copied back from
            the tick node(s). By default this will be job_dir/results

        ``jobname`` : string
            Name associated with the job in the PBS system. By default it will
            be the parent folder's name.

        ``ncpu`` : integer (default = 1)
            Number of cores requested. Currently there is no support for more
            than one node. But this can be changed easily in the jobfilestring.

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

        ``export_host`` : string(default=None)
            The host holding the export dir in the line above. Only effective,
            if no export_dir is given.

        ``copyback_export`` : List of strings (default = [''])
            Files that are copied back to the export path given by `export_dir`.
            Wildcards are supported.

        ``check_consistency`` : Boolean (default = True)
            ...CASTEP/AIMS only...
            Check for input consistency (if *.cell and *.param file exist).
            Additionally, adds the RUM_TIME flag with the appropriate walltime
            specified to the *.param file if not already specified.

        ``debug`` : Boolean (default = False)
            Print each executed command and full environment to PBS outfile.

        ``cleanup`` : Boolean (default = True)
            Delete temporary folder from the tick after all requested files
            have been copied back successfully.

        ``dryrun`` : boolean (Default = False)
            If True, job will not be run, ie. the execution on the bash will be
            omitted.
        """

        # same for the required list, but here we can simply go via sets
        self.required = ['program']

        # it is better to have this thing an instance variable rather than a
        # class variable
        self.defaults = {
                         "ncpu": 1,
                         "copy": ['*'],
                         "copyback": ['*'],
                         "copyback_export": [],
                         "export_dir": "",
                         "dryrun": False,
                         "debug": False,
                         "check_consistency": True,
                         "result_dir": ".",
                         "infofile": "workstation.info",
                         "jobname" : None,
                         "job_dir" : os.path.abspath(os.getcwd()),
                         "cleanup": True,
                         "export_host" : os.uname()[1]
                         }

        # internal placeholder
        self._jobfilename = None
        self._user = os.environ["USER"]  # os.getlogin()
        self._host = os.uname()[1]

        # let the parent do it's job
        super(WorkstationAgent, self).__init__(init_params=True, **kwargs)
        self._check_input_sanity()

        self._export_host = self.params['export_host']

        self.bash_dict = self._get_bash_template()


    def _check_input_sanity(self):
        # just check for a proper pbs name here
        self.params['job_dir'] = os.path.abspath(self.params['job_dir'])


    def submit(self):
        """write the pbs file and submit the job"""
        self._write_bash()
        self._run_job()

    # Methods to write the files and submit the job (as well as consistency
    # checks
    def _format_bash_template(self):
        """
        Return the bash file string with all placeholders replaced with
        the actual values.
        """
        jobfilestring = ""
        formatdict = dict()
        for value in self.bash_dict.values():
            jobfilestring += value

        keys = list([i[1] for i in Formatter().parse(jobfilestring)
                     if i[1] is not None])
        for key in keys:
            formatdict[key] = getattr(self, key.lower())()

        bashstring = jobfilestring.format(**formatdict)
        return bashstring

    def _write_bash(self):
        """
        Write the actual bash file. The name is determined by the host and jobname.
        """
        self._jobfilename = 'job.' + self.params['jobname'] + '.sh'
        jobfile = os.path.join(self.params['job_dir'], self._jobfilename)
        bashstring = self._format_bash_template()
        with open(jobfile, 'w') as f:
            f.write(bashstring)

    def _run_job(self):
        cwd = os.getcwd()
        os.chdir(self.params['job_dir'])

        if self.params["dryrun"]:
            print('Prepared but not run (job name "{}")'.format(
                self.params['jobname']))
            out = '-1'
        else:
            starttime = time.time()
            # well... in python 3.3 we could directly flush via print...
            print('Running job "{}"... '.format(self.params['jobname']), end ='')
            sys.stdout.flush()
            with open(os.path.join(self.params['job_dir'],
                                   self.params['infofile']), 'w') as f:
                f.write('job prepared at {}'.format(time.strftime('%c')))
                f.write('\n')
                f.write('\nuser   : {}'.format(self._user))
                f.write('\nhost : {}'.format(self._host))
                f.write('\n')

            outfile=os.path.join(self.params['job_dir'], 'log.' + self.params['jobname'] + '.{}.o'.format(int(time.time()*1e3)))
            out = subprocess.check_output('bash {} > {} 2>&1'.format(self._jobfilename, outfile),
                                          shell=True)
            print('done ({})'.format(format_timing(starttime, time.time())))
            sys.stdout.flush()

        os.chdir(cwd)


    # All methods for the PBS template formatters

    def _tp_ncpu(self):
        """Get the number of CPUs per node per job"""
        return int(self.params.get("ncpu"))

    def _tp_debug(self):
        """Get the debug toggle."""
        if self.params.get("debug"):
            return ""
        else:
            return "# "

    def _tp_cleanup(self):
        """Get the toggle for automatic cleanup."""
        if self.params.get("cleanup"):
            return " "
        else:
            return "# "
    def _tp_jobname(self):
        """Get the job title"""
        return self.params['jobname']

    def _tp_jobfolder(self):
        """Get the job folder"""
        return self.params['job_dir']

    def _tp_result_dir(self):
        """Get the result folder, default to self.params['job_dir']"""
        result_dir = self.params["result_dir"]

        # we aim for ${jobdir}/${result_dir} in the bash script as this is more
        # convenient when manually editing something in there. It is hard-coded
        # to be a sub folder of job_dir anyway.
        # Hence the version with the underscore is just a dummy to check if the
        # folder exists or not
        _result_dir = os.path.join(self.params['job_dir'], result_dir)
        if not os.path.isdir(_result_dir):
            os.makedirs(_result_dir)

        return result_dir

    def _tp_export_dir(self):
        """Get the local export dir."""
        if self.params["export_dir"] != "":
            export_dir = os.path.abspath(self.params["export_dir"])
        else:
            export_dir = self.params['job_dir'].replace(
                '/data/{}/'.format(self._user),
                '/net/{}/export/{}/'.format(self._export_host,
                                            self._user))
        if self.params["copyback_export"] and not\
                os.path.isdir(export_dir):
            os.makedirs(export_dir)
        elif self.params["copyback_export"] and not os.access(
                export_dir, os.W_OK):
            raise OSError('No  write access to `export_dir`:\n{}'.format(
                export_dir))
        return export_dir

    def _tp_copyback_export(self):
        """Get all files to copy back to local export dir after job finished."""
        copyback_export_str = \
            " ".join(map(str, self.params["copyback_export"]))
        return copyback_export_str

    def _tp_doexportcopy(self):
        """Get the actual copy command for local export copy."""
        if len(self.params["copyback_export"]) != 0:
            # not necessary as the folder will be created on the python level
            #export_copy_str = r'mkdir -p $exportfolder || :'+'\n'
            export_copy_str = r'cp -a $exportoutput $exportfolder'
        else:
            export_copy_str = r'# --> nothing will be copied to export'
        return export_copy_str

    def _tp_copy(self):
        """Get all files to copy."""
        copy_str = self.params["copy"]
        if isinstance(copy_str, list):
            copy_str = " ".join(map(str, copy_str))

        if copy_str == "*":  # catch wildcard copy and exclude result dir
            all_copy = [os.path.basename(x) for
                        x in glob.glob(os.path.join(self.params['job_dir'], copy_str))]

            if self.params["result_dir"] in all_copy:
                all_copy.remove(self.params["result_dir"])

            copy_str = " ".join(map(str, all_copy))

        return copy_str

    def _tp_copyback(self):
        """Get all files to copy back after job finished"""
        copyback_str = self.params["copyback"]
        if isinstance(copyback_str, list):
            copyback_str = " ".join(map(str, copyback_str))
        return copyback_str

    def _tp_setupcommands(self):
        """Get additional setup for PBS jobs in environment section."""
        set_str = ""
        for item in self.setupcommands:
            set_str += "{}\n".format(item)
        return set_str

    def _tp_infofile(self):
        """
        The infofile in which we write info from the PBS system and the nodes.
        """
        infofile_str = self.params['infofile']
        return infofile_str


    def _get_bash_template(self):
        """
        The bash template string for the bash submit version.

        This template can be extended and new formatters ({_TP_FORMATTER}) can
        be added. For each new formatter, a class method must be provided with
        the name of the formatter.

        Example
        -------
        To add "{_TP_SUPERFOO}" at some place in the template, define a new
        class method:

        >>> def superfoo(self, "yourfoo"):
                #do some fancy foo
                return foo_string
        """
        bash_dict = OrderedDict()
        bash_dict["BASH"] = r"""#!/usr/bin/env bash
#-----------------------------------------------------------------------------+
# local "submit" script written by rtools                                     |
#                                                                             |
# Simon P. Rittmeyer (TUM)                                                    |
#-----------------------------------------------------------------------------+

"""

        bash_dict["COPY_SETUP"] = r"""##################################################################
#---INPUT---
jobfolder={_TP_JOBFOLDER}

#---OUTPUT---
resultfolder=$jobfolder/{_TP_RESULT_DIR}
exportfolder={_TP_EXPORT_DIR}

#---INPUT/OUTPUT---
# files that are copied to the temporary directory
input="{_TP_COPY}"
# files that are copied back into the resultfolder
output="{_TP_COPYBACK}"
# files that are copied to the exportfolder
exportoutput="{_TP_COPYBACK_EXPORT}"
##################################################################
"""

        bash_dict["ENV"] = r"""# environment variable setup
{_TP_SETUPCOMMANDS}
{_TP_ENVIRONMENT}

program={_TP_PROGRAM}
nproc={_TP_NCPU}

FROM=$jobfolder                 # directory holding all neccessary input
DEST=$resultfolder              # destination directory for the results
                                # don't use a directory under $HOME for these!
                                # It won't work with AFS

# create the temporary directory
TMPDIR=$(mktemp -d -p /scratch/${{USER}})

export FROM DEST TMPDIR

{_TP_DEBUG}printenv                 # uncomment to see all environment variables
{_TP_DEBUG}set -x                   # uncomment to get all commands echo'ed

# some io in case you want to recover/retrace jobs that failed

# we need a sleep second here in order to give the submit agent enough time to
# close the file
sleep 1

infofile=$FROM/{_TP_INFOFILE}

echo "" >> $infofile
echo "job started at $(date)" >> $infofile
echo "" >> $infofile
echo "running as ${{USER}}@${{HOSTNAME}}" >> $infofile
echo "" >> $infofile
echo "local working directory" >> $infofile
echo "-----------------------" >> $infofile
echo "${{TMPDIR}}" >> $infofile

"""

        bash_dict["COPY"] = r"""# Here the real job starts
#
echo "#--- Job started at `date`"

cd $FROM || exit 2

# copy all necessary files (input, source, programs etc.) to the execution
# host (links will be copied as links!)
cp -r $input $TMPDIR

# run the job locally on the execution host (not on data.. minimize network traffic)
cd $TMPDIR

"""

        bash_dict["PRE_CMD"] = r"""# custom pre-command stuff
{_TP_PRECOMMAND}
"""

        bash_dict["CMD"] = r"""# run, Forest, run,...
{_TP_COMMAND}
"""

        bash_dict["POST_CMD"] = r"""# custom post-command stuff
{_TP_POSTCOMMAND}
"""
        bash_dict["COPY_BACK"] = r"""# copy all output files from the execution host back to $DEST
cp -a $output $DEST

# if requested, copy files to local export directory
{_TP_DOEXPORTCOPY}

# remove the temporary directory if $DEST is accessible
{_TP_CLEANUP}cd $DEST && rm -rf $TMPDIR # uncomment this for automatic cleanup

echo "#--- Job ended at `date`"

echo "" >> $infofile
echo "job ended at $(date)" >> $infofile
"""
        return bash_dict


def get_defaults(agent, **required_arguments):
    """
    Collect default values from SubmitAgent class and default file and
    return them to be displayed.

    Parameters
    ----------
    agent : object or str
        The actual class or a string with the name of the class to test.
    required_arguments : key,value pairs
        All arguments required by the Agent (no optional arguments needed)

    Returns
    -------
    defaults : dict
        All defined defaults.
    """
    if isinstance(agent, str):
        mod_str = "rtools.submitagents.arthur.{}".format(agent.lower())
        module = importlib.import_module(mod_str)
        ag = getattr(module, agent.lower().capitalize())
        required_arguments["check_consistency"] = False
        required_arguments["dryrun"] = True
        try:
            with open(os.devnull, "w") as f:
                old_stdout = sys.stdout
                sys.stdout = f
                R = ag(**required_arguments)
                defaults = R.defaults
        finally:
            f.close()
            sys.stdout = old_stdout
    else:
        raise NotImplementedError("This function is not yet implemented\
for objects.")
    return defaults


def default_argparse():
    """
    Return a default argparse parser with common options for submit scripts.
    """
    pa = argparse.ArgumentParser(description="Arguments for PBS submit script.")

    pa.add_argument('-n', '--ncpu', help='The number of CPUs.',
                    dest='ncpu', type=int)
    pa.add_argument('-N', '--jobname', help='The PBS job title. If not given,\
                    current foldername will be used.',
                    dest='jobname', type=str)
    pa.add_argument('-p', '--program', help='Path to program binary. Either this\
                    option or a default value in\
                    ~/.rtools/defaults must be set.',
                    dest='program', type=str)
    pa.add_argument('-j', '--job_dir', help='The jobfolder with prepared inputs.\
                    Default: Current working directory.',
                    dest='job_dir', type=str)
    pa.add_argument('-r', '--result_dir', help='Folder where the output specified by\
                    `copyback` is copied back from the tick node(s). \
                    By default this will be job_dir',
                    dest='result_dir', type=str)
    pa.add_argument('-c', '--copy', help='All files which should be copied TO the \
                    cluster (e.g. input files, ...)',
                    dest='copy', nargs='+')
    pa.add_argument('-b', '--copyback', help='All files to be copied BACK from the\
                    cluster (e.g. result files, checkpoint files, etc)',
                    dest="copyback", nargs='+')
    pa.add_argument('-d', '--dryrun', help='Boolean. If given, only prepare\
                    PBS job script without submitting to Arthur.',
                    dest="dryrun", action="store_true")
    pa.add_argument('--check_consistency', help='Boolean. If given, check for\
                    missing input files and input consistency.',
                    dest='check_consistency', action='store_true')
    pa.add_argument('--no-check_consistency', help='Boolean. If given, do not\
                    check for missing input files and input consistency.',
                    dest='check_consistency', action='store_false')
    pa.add_argument('--export_dir', help='A export directory for large files on\
                    your local computers hdd (usually /export/username)',
                    dest='export_dir', type=str)
    pa.add_argument('--copyback_export', help='The files which should be\
                    copied back to the local export.',
                    dest='copyback_export', nargs='+')
    return pa
