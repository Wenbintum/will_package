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

from rtools.submitagents import Agent
from rtools.submitagents import check_email_address


class ArthurAgent(Agent):
    """Base-class for all submitagents for different codes/tasks.

    An agent is supposed to handle the task of creating and
    submitting a job file to our local Arthur-cluster (PBS queuing).

    ---
    Christoph Schober, Simon P. Rittmeyer (TUM), 2015.
    """

    _avail_features = ['Intel',
                       'AMD',
                       'jessie',
                       'Opteron6272',
                       'Opteron2435',
                       'Opteron6172',
                       'XeonE5640',
                       'XeonE5540',
                       'em64t',
                       'amd64',
                       'x86_64',
                       'opteron',
                       'xeon',
                       'smp']

    @property
    def avail_features(self):
        return self._avail_features

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
            the tick node(s). By default this will be job_dir

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
            Check for input consistency.
            Additionally, adds the RUM_TIME/walltime flag with the appropriate
            walltime specified to the *.param/control.in file if not already
            specified.

        ``debug`` : Boolean (default = False)
            Print each executed command and full environment to PBS outfile.

        ``cleanup`` : Boolean (default = False)
            Delete temporary folder from the tick after all requested files
            have been copied back successfully.

        ``infofile`` : str (default = "arthur.info")
            The file which will contain information such as the PBS job id, the
            nodes on which your job actually runs and the local working
            directory on these nodes. Will be appended the PBS job id, the fill
            will thus be `<infofile>.<pbs_id>`

        ``dryrun`` : boolean (Default = False)
            If True, job will not be submitted, ie. the qsub command is
            omitted. Automatically set False if `return_id` is True.
        """

        # same for the required list, but here we can simply go via sets
        self.required = ['program']

        # it is better to have this thing an instance variable rather than a
        # class variable
        self.defaults = {"walltime": "01:00:00",
                         "ncpu": 1,
                         "memory": "1000mb",
                         "copy": ['*'],
                         "copyback": ['*'],
                         "copyback_export": [],
                         'export_variables' : {},
                         "export_dir": "",
                         "node_features": [],
                         "exclude_nodes": [],
                         "email": True,
                         "email_address": None,
                         "dryrun": False,
                         "debug": True,
                         "check_consistency": True,
                         "result_dir": ".",
                         "job_dir" : os.path.abspath(os.getcwd()),
                         "pbsname" : None,
                         "infofile": "arthur.info",
                         "cleanup": False
                         }

        self._user = os.environ["USER"]  # os.getlogin()
        self._host = os.uname()[1]

        # internal placeholder
        self._jobfilename = None

        # let the parent do it's job
        super(ArthurAgent, self).__init__(init_params=True, **kwargs)
        self._check_input_sanity()
        self._expand_environment()

        self.pbs_dict = self._get_pbs_template()


    def _check_input_sanity(self):
        # check if we have an explicit email address
        if self.params['email_address'] is not None:
            check_email_address(self.params['email_address'])
            self.params['email'] = True
        else:
            self.params['email_address'] = self._user

        # just check for a proper pbs name here
        self.params['job_dir'] = os.path.abspath(self.params['job_dir'])

        if self.params['pbsname'] is None:
            self.params['pbsname'] = os.path.basename(self.params['job_dir'])


    def submit(self):
        """write the pbs file and submit the job"""
        self._write_pbs()
        return self._submit_job()

    # Methods to write the files and submit the job (as well as consistency
    # checks
    def _format_pbs_template(self):
        """
        Return the PBS submit file string with all placeholders replaced with
        the actual values.
        """
        jobfilestring = ""
        formatdict = dict()
        for value in self.pbs_dict.values():
            jobfilestring += value

        keys = list([i[1] for i in Formatter().parse(jobfilestring)
                     if i[1] is not None])
        for key in keys:
            formatdict[key] = getattr(self, key.lower())()

        pbsstring = jobfilestring.format(**formatdict)
        return pbsstring

    def _write_pbs(self):
        """
        Write the actual job file. The name is determined by the PBS-name.
        """
        self._jobfilename = 'job.' + self.params['pbsname'] + '.arthur'
        jobfile = os.path.join(self.params['job_dir'], self._jobfilename)
        pbsstring = self._format_pbs_template()
        with open(jobfile, 'w') as f:
            f.write(pbsstring)

    def _submit_job(self):
        cwd = os.getcwd()
        os.chdir(self.params['job_dir'])

        if self.params["dryrun"]:
            print('Prepared but not submitted (PBS title "{}")'.format(
                self.params['pbsname']))
            out = '-1'
        else:
            out = subprocess.check_output('qsub {}'.format(self._jobfilename),
                                          shell=True)
            out = out.strip('\n').split('.')[0]
            print('Submitted with PBS title "{}" (job id: {})'.format(
                self.params['pbsname'], out))
            with open(os.path.join(self.params['job_dir'],
                                   self.params['infofile'] + '.{}'.format(out)), 'w') as f:
                f.write('job submitted at {}'.format(time.strftime('%c')))
                f.write('\n')
                f.write('\npbs job id   : {}'.format(out))
                f.write('\npbs job name : {}'.format(self.params['pbsname']))
                f.write('\n')

        os.chdir(cwd)
        return out


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
    def _tp_pbsname(self):
        """Get the PBS title"""
        return self.params['pbsname']

    def _tp_email(self):
        """Get the email option for notification from PBS"""
        mail = self.params["email"]
        if mail:
            m_str = r'#PBS -m ae'
        else:
            m_str = r'##PBS -m ae'
        return m_str

    def _tp_user(self):
        """Get the user name"""
        return self._user

    def _tp_email_address(self):
        return self.params['email_address']

    def _tp_node_features(self):
        """Get all requested node features and return a PBS conform string."""
        node_features = self.params.get("node_features", "")
        node_features_str = ""
        if isinstance(node_features, str):
            node_features = [node_features]
        for f in node_features:
            if f in self.avail_features:
                node_features_str += ':{}'.format(f)
            else:
                err_msg = "unknown node feature: \
                    ``{}'' (will be disregarded)".format(f)
                print('\t'+err_msg)

                alternatives = get_close_matches(f, self.avail_features)
                print(alternatives)

        return node_features_str

    def _tp_exclude_nodes(self):
        """Get all excluded nodes and return a PBS conform string."""
        exclude_nodes = self.params.get("exclude_nodes", "")
        if exclude_nodes:
            if isinstance(exclude_nodes, str):
                exclude_nodes = [exclude_nodes]

            exclude_nodes_str = r'# exclude nodes'+'\n'+r'#$ -l h=' + '&'.join(['!'+e for e in exclude_nodes])
        else:
            exclude_nodes_str = "# no nodes excluded"
        return exclude_nodes_str


    def _tp_memory(self):
        """
        Get the memory, only in MB as int/float or string with unit (mb, gb)
        """
        mem = self.params["memory"]
        if not isinstance(mem, str):
            mem = "{}gb".format(int(mem))
        return mem

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
                '/net/{}/export/{}/'.format(self._host,
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
            # .o and .e PBS files
            r = re.compile(r'.*\.[oe][0-9]{7}|arthur\.(jobid|ticks)|job\..+\.arthur')
            all_copy = [x for x in all_copy if not r.search(x)]

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


    def _get_pbs_template(self):
        """
        The PBS template string for the bash submit version.

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
        pbs_dict = OrderedDict()
        pbs_dict["PBS"] = r"""#!/bin/sh
#-----------------------------------------------------------------------------+
# submit script written by rtools                                             |
#                                                                             |
# Simon P. Rittmeyer (TUM)                                                    |
# Christoph Schober (TUM)                                                     |
#-----------------------------------------------------------------------------+
#
#PBS -N {_TP_PBSNAME}
#PBS -S /bin/sh
#PBS -j oe
{_TP_EMAIL}
#PBS -M {_TP_EMAIL_ADDRESS}
#PBS -l walltime={_TP_WALLTIME},nodes=1:ppn={_TP_NCPU}{_TP_NODE_FEATURES},pmem={_TP_MEMORY}
{_TP_EXCLUDE_NODES}
"""

        pbs_dict["COPY_SETUP"] = r"""##################################################################
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

        pbs_dict["ENV"] = r"""# environment variable setup
{_TP_SETUPCOMMANDS}
{_TP_ENVIRONMENT}

program={_TP_PROGRAM}

FROM=$jobfolder                   # directory holding all neccessary input
DEST=$resultfolder                # destination directory for the results
                                  # don't use a directory under $HOME for these!
                                  # It won't work with AFS
JOBID=$(echo ${{PBS_JOBID%%.*}})  # Only the ID, without any further info
LOCALDIR=$TMPDIR/$JOBID           # local work directory on the execution host
export FROM DEST LOCALDIR JOBID

# mpi bug on stretch images
export TMPDIR=/scratch/${{USER}}


# some io in case you want to recover/retrace jobs that failed

# we need a sleep second here in order to give the submit agent enough time to
# close the file
sleep 1

infofile=$FROM/{_TP_INFOFILE}.$JOBID

echo "" >> $infofile
echo "job started at $(date)" >> $infofile
echo "" >> $infofile

TICK=`tail -1 $PBS_NODEFILE`

echo "invoked tick nodes" >> $infofile
echo "------------------" >> $infofile
cat $PBS_NODEFILE >> $infofile    # this file contains the nodes that
                                  # were allocated for your job if you
                                  # use MPI or PVM
echo "" >> $infofile
echo "local working directory" >> $infofile
echo "-----------------------" >> $infofile
echo "/net/$TICK/$LOCALDIR" >> $infofile

{_TP_DEBUG}printenv                 # uncomment to see all environment variables
{_TP_DEBUG}set -x                   # uncomment to get all commands echo'ed

"""

        pbs_dict["COPY"] = r"""# Here the real job starts
#
echo "#--- Job started at `date`"

# create the temporary directory and make sure the input directory is
# accessible
mkdir -p $LOCALDIR || exit 1
cd $FROM || exit 2

# copy all necessary files (input, source, programs etc.) to the execution
# host (links will be copied as links!)
cp -r $input $LOCALDIR

# run the job locally on the execution host
cd $LOCALDIR

"""

        pbs_dict["PRE_CMD"] = r"""# custom pre-command stuff
{_TP_PRECOMMAND}
"""

        pbs_dict["CMD"] = r"""# run, Forest, run,...
{_TP_COMMAND}
"""

        pbs_dict["POST_CMD"] = r"""# custom post-command stuff
{_TP_POSTCOMMAND}
"""
        pbs_dict["COPY_BACK"] = r"""# copy all output files from the execution host back to $DEST
cp -a $output $DEST

# if requested, copy files to local export directory
{_TP_DOEXPORTCOPY}

# remove the temporary directory if $DEST is accessible
{_TP_CLEANUP}cd $DEST && rm -rf $LOCALDIR # uncomment this for automatic cleanup

echo "#--- Job ended at `date`"

echo "" >> $infofile
echo "job ended at $(date)" >> $infofile
"""
        return pbs_dict


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

    pa.add_argument('-t', '--walltime', help='The required walltime in hours',
                    dest='walltime', type=int)
    pa.add_argument('-n', '--ncpu', help='The number of CPUs.',
                    dest='ncpu', type=int)
    pa.add_argument('-m', '--memory', help='The amount of memory per CPU as\
                    string with unit, e.g. 500mb or 2gb',
                    dest='memory', type=str)
    pa.add_argument('-N', '--pbsname', help='The PBS job title. If not given,\
                    current foldername will be used.',
                    dest='pbsname', type=str)
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
    pa.add_argument('-e', '--email', help='Boolean. If given, send PBS job emails.\
                    This is the default.',
                    dest='email', action='store_true')
    pa.add_argument('-f', '--node_features', help='string or list of strings with\
                    PBS node features (example: jessie xeon)',
                    dest='node_features', type=str, nargs='+')
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
