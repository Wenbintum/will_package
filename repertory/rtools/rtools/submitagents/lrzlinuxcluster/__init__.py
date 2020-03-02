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
Base class to submit jobs to the SLURM Batch Loader running on the LRZ Linux Cluster
"""

from __future__ import print_function

import argparse
import importlib
import os
import glob
import subprocess
import time
import re
import sys
from configparser import SafeConfigParser
from collections import OrderedDict, MutableSequence, MutableMapping
from copy import copy
from string import Formatter

from rtools.submitagents import Agent
from rtools.submitagents import check_email_address

def resolve_home_work_vars(string):
    """
    make sure there is no "~" in the jobfolder, and if so, replace it
    with environ["HOME"]. also resolve $WORK
    """
    string = re.sub(r'(~|\$HOME|\${HOME})',
                    os.environ['HOME'],
                    string)

    if 'WORK' in os.environ.keys():
        string = re.sub(r'\$WORK|\${WORK}',
                        os.environ['WORK'],
                        string)
    return string


class LinuxClusterAgent(Agent):
    """
    Class to submit jobs to the SLURM batch loader on the LRZ Linux Cluster.
    Very similar to the arthur submit agent, but implemented more recently.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = LinuxClusterAgent(*args, **kwargs)
        >>> # this writes the jobfile and submits it to the batch loader
        >>> agent.submit()

    Initialization
    --------------
    ``program'' : string
        Program to be executed. Note that you either have to provide a full
        path, or that you have to export corresponding variables (see
        ``export_variables''). The SLURM shell does *NOT* inherit any paths you
        have set in the calling shell.

    ``walltime'' : string or integer
        The required walltime. Either a string in format "hh:mm:ss" or an
        integer which will then be interpreted as hours.

    ``clusters'' : string ({"mpp1", *"mpp2"*, "serial"})
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
    # available clusters and cpu per node (always complete node allocation)
    # this is not a complete list, but that of available clusters for project pr47fo
    _avail_clusters = {'mpp1' :   {'cpu_per_node' : 16,
                                   'login_node' : r'lxlogin(1|2).*' # to be submitted from lxlogin(1|2).lrz
                                  },
                       'mpp2' :   {'cpu_per_node' : 28,
                                   'login_node' : r'lxlogin(5|6).*' # to be submitted from lxlogin(5|6).lrz
                                  },
                       'serial' : {'cpu_per_node' : 1,
                                   'login_node' : r'lxlogin(5|6|7).*'
                                  }
                       }

    def __init__(self, **kwargs):
        """
        Initialize the agent. For details on the **kwargs please see the class doc.
        """
        # we do it a bit different than for the arthur agent:
        # defaults carries *ALL* arguments
        # anything that has to be specified by the USER is of value <None> and
        # in self._required. This allows for a more consistent handling.
        self.defaults = {'walltime': None,
                         'nnodes': None,
                         'clusters' : None,
                         'clean': [],
                         'email_address': None,
                         'dryrun': False,
                         'debug': True,
                         'check_consistency': True,
                         'outfile': None,
                         'load_modules' : [],
                         'unload_modules' : [],
                         'export_variables' : {},
                         'slurmname' : None,
                         'program' : None,
                         'dependency' : None,
                         'job_dir' : os.path.abspath(os.getcwd())
                         }

        self.required = ['walltime',
                         'program',
                         'nnodes',
                         'clusters',
                         'email_address',
                        ]

        # let the parent do it's job, we do the explicit init here
        super(LinuxClusterAgent, self).__init__(init_params=True, **kwargs)

        self.slurm_dict = self._get_slurm_template()

    # add the sanity check to the parent's version
    def _init_params(self, kwargs):
        super(LinuxClusterAgent, self)._init_params(kwargs)
        self._check_input_sanity()
        self._expand_environment()

    def _check_input_sanity(self):
        # sanity check for the jobfolder
        # make sure there is no "~" in the jobfolder, and if so, replace it
        # with environ["HOME"]

        self.params['job_dir'] = resolve_home_work_vars(self.params['job_dir'])
        self.params['job_dir'] = os.path.abspath(self.params['job_dir'])

        if self.params['slurmname'] is None:
            self.params['slurmname'] = os.path.basename(self.params['job_dir'])

        # check for max lenght of slurm name
        slurmname = self.params['slurmname']
        if len(slurmname) > 10:
            slurmname = slurmname[0:10]
            print('"slurmname" variable exceeds 10 characters. Will be shortened to "{}"'.format(slurmname))
            self.params['slurmname'] = slurmname

        # check for the clusters
        clusters = self.params['clusters'].lower()
        if clusters in self._avail_clusters.keys():
            self.params['clusters'] = clusters
        else:
            raise NotImplementedError('Support for "{}" clusters not implemented'.format(clusters))

        # check for valid mail format
        check_email_address(self.params['email_address'])

        # check for paths in environment
        for key, val in self.params['export_variables'].items():
            self.params[key]=resolve_home_work_vars(val)

        self.params['program'] = resolve_home_work_vars(self.params['program'])

    # SR: moved to base class
    # def _expand_environment(self):
        # for key, val in self.params['export_variables'].items():
            # # make sure we put quotation marks around the thing
            # #if len(val.split()) > 1:
            # val = '"{}"'.format(val.strip('"').strip("'"))
            # self.environment.add(key.strip(), val)


    # the templates
    def _tp_outfile(self):
        outfile = os.path.join(self.params['job_dir'],
                               '{}.%j.%N.out'.format(self.params['slurmname'])
                               )
        return outfile


    def _tp_jobfolder(self):
        return self.params['job_dir']

    def _tp_slurmname(self):
        return self.params['slurmname']

    def _tp_ncpu(self):
        return int(self.params['nnodes']) * self._avail_clusters[self._tp_clusters()]['cpu_per_node']

    def _tp_clusters(self):
        return self.params['clusters']

    def _tp_email(self):
        return self.params['email_address']

    def _tp_modules(self):
        if self.params['load_modules'] or self.params['unload_modules']:
            modules = '# initialize the module system'
            modules += '\nsource /etc/profile.d/modules.sh\n'

            modules += '\n# unloading modules'
            for m in list(self.params['unload_modules']):
                modules += '\nmodule unload {0}'.format(m)

            modules += '\n# loading user modules'

            for m in list(self.params['load_modules']):
                modules += '\nmodule load {0}'.format(m)

            modules += '\n# list all modules'
            modules += '\nmodule list'
        else:
            modules = '# no user defined modules'
        return modules

    def _tp_cleanup(self):
        clean_str = self.params['clean']
        if isinstance(clean_str, list):
            clean_str = " ".join(map(str, clean_str))

        elif clean_str == "*":  # catch wildcard copy and exclude result dir
            raise ValueError('You cannot clean the entire directory, that is pointless!')

        if clean_str:
            return "rm -rf {}".format(clean_str)
        else:
            return "# nothing to clean"


    def _get_slurm_template(self):
        """
        The SLURM template string for the bash submit version.

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
        slurm_dict = OrderedDict()
        slurm_dict["SLURM"] = r"""
#!/bin/bash

#-----------------------------------------------------------------------------+
# submit script written by rtools                                             |
#                                                                             |
# for details see                                                             |
#     http://www.lrz.de/services/compute/linux-cluster/batch_parallel/        |
#                                                                             |
# Simon P. Rittmeyer (TUM), 2016                                              |
#-----------------------------------------------------------------------------+

#-----------------------------------------------------------------------------+
# SLURM CONFIGURATION                                                         |
#-----------------------------------------------------------------------------+

# stderr and stdout
#SBATCH -o {_TP_OUTFILE}

# starting directory a.k.a. working directory
#SBATCH -D {_TP_JOBFOLDER}

# job name
#SBATCH -J {_TP_SLURMNAME}

# cluster used
#SBATCH --clusters={_TP_CLUSTERS}

# set environment properly
#SBATCH --get-user-env

# do not export environment of the submitting shell
#SBATCH --export=NONE

# number of MPI tasks assigned to the job
# use multiples of 28 for mpp2 or multiples of 16 for mpp1
#SBATCH --ntasks {_TP_NCPU}

# user config
#SBATCH --mail-type=end
#SBATCH --mail-user={_TP_EMAIL}

# walltime
#SBATCH --time={_TP_WALLTIME}
"""[1::]

        slurm_dict['MODULES'] = r"""
#-----------------------------------------------------------------------------+
# THE ACTUAL JOB PROCESSING                                                   |
#-----------------------------------------------------------------------------+

echo "#--- Job started at `date`"

## modules
{_TP_MODULES}

# this one echos each command (only after module scripts!)
set -x
"""

        slurm_dict['ENV'] = r"""
# environment variables
{_TP_ENVIRONMENT}

# the actual binary that is run
program={_TP_PROGRAM}
"""

        slurm_dict['PRE_CMD'] = r"""
# custom pre-command stuff
{_TP_PRECOMMAND}
"""

        slurm_dict['CMD'] = r"""
# run, Forest, run,...
{_TP_COMMAND}
"""[1::]

        slurm_dict['POST_CMD'] = r"""
# custom post-command stuff
{_TP_POSTCOMMAND}
"""[1::]

        slurm_dict['CLEAN'] = r"""
# remove the requested files
{_TP_CLEANUP}

echo "#--- Job ended at `date`"
"""[1::]

        return slurm_dict

    # Methods to write the files and submit the job (as well as consistency
    # checks
    def _format_slurm_template(self):
        """
        Return the SLURM submit file string with all placeholders replaced with
        the actual values.
        """
        jobfilestring = ""
        formatdict = dict()
        for value in self.slurm_dict.values():
            jobfilestring += value

        keys = list([i[1] for i in Formatter().parse(jobfilestring)
                     if i[1] is not None])
        for key in keys:
            formatdict[key] = getattr(self, key.lower())()

        slurmstring = jobfilestring.format(**formatdict)
        return slurmstring


    def _write_slurm(self):
        """
        Write the actual job file. The name is determined by the PBS-name.
        """
        self._jobfilename = 'job.' + self.params['slurmname'] + '.linuxcluster'
        jobfile = os.path.join(self.params['job_dir'], self._jobfilename)
        slurmstring = self._format_slurm_template()
        with open(jobfile, 'w') as f:
            f.write(slurmstring)

    def _submit_job(self):
        cwd = os.getcwd()
        os.chdir(self.params['job_dir'])

        cluster = None
        job_id = None

        if self.params["dryrun"]:
            print('Prepared but not submitted (SLURM title "{}")'.format(self.params['slurmname']))
        else:
            cmd = 'sbatch'
            if self.params['dependency'] is not None:
                cmd += ' --dependency={}'.format(self.params['dependency'])
            cmd += ' {}'.format(self._jobfilename)
            out = subprocess.check_output(cmd, shell=True)
            out = out.strip('\n')
            pattern=r'Submitted batch job ([\d]+) on cluster ([\w]+)'
            job_id, cluster = re.search(pattern, out).groups()

            print('Submitted with to "{}" with SLURM title "{}" (job id: {})'.format(
                cluster, self.params['slurmname'], job_id))
        os.chdir(cwd)

        return cluster, job_id

    def submit(self):
        """write the slurm file and submit the job"""
        self._write_slurm()
        return self._submit_job()
