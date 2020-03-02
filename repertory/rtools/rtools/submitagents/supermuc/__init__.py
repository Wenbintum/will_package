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
Base class to submit jobs to the LoadLeveler Batch Loader running on LRZ SuperMUC
"""

from __future__ import print_function

import os
import subprocess
import re
import warnings

from collections import OrderedDict
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


class SuperMucAgent(Agent):
    """
    Class to submit jobs to the LoadLeveler batch loader on the LRZ Linux Cluster.
    Very similar to the arthur submit agent, but implemented more recently.

    The main usage is as follows:

        >>> # this creates an agent instance
        >>> agent = SuperMucAgent(*args, **kwargs)
        >>> # this writes the jobfile and submits it to the batch loader
        >>> agent.submit()

    Initialization
    --------------
    ``program'' : string
        Program to be executed. Note that you either have to provide a full
        path, or that you have to export corresponding variables (see
        ``export_variables''). The node-shell does *NOT* inherit any paths you
        have set in the calling shell.

    ``walltime'' : string or integer
        The required walltime. Either a string in format "hh:mm:ss" or an
        integer which will then be interpreted as hours.

    ``email_address'' : string
        Your mail address to which notifications are sent. This is a
        requirement on LRZ systems.


    ``architecture'' : string ({"fat", "thin", *"phase2"*})
        The node-architecture this job shall be submitted to. Clusters differ in node
        architecture and in available memory and CPU per node. More details can
        be found here:

            https://www.lrz.de/services/compute/supermuc/loadleveler/

        Note that you cannot necessarily submit to each cluster from each login
        node.

    ``job_class'' : string
        Job class. Depends on the node architecture you choose.
            'thin' : ['test', 'general', 'large']
            'fat' : ['fattest', 'fatter', 'fat']
            'phase2' : ['test', 'micro', 'general', 'big']
        More details here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#jobclass

    ``nnodes'' : integer
        The number of requested nodes. The actual number of available CPU and
        memory depends on the cluster you submit to.

    ``ntasks'' : integer, optional (default=None)
        The total number of requested tasks, ie., processes. Cannot be combined
        with ntasks_per_node. If <None>, it will be max node cpu * nnodes
        See also here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#TOC

    ``ntasks_per_node'' : integer, optional (default=None)
        The number of requested tasks, ie., processes per node. Cannot be
        combined with ntasks. If <None> it will be max node cpu.
        See also here:
            https://www.lrz.de/services/compute/supermuc/loadleveler/#TOC

    ``island_count'' : list of two integer [min, max] (default = None)
        If you require more than one island (512 nodes!), specify here the
        minimum and maximum island count.

    ``notification'' : string, optional ({"always", "error", "start", "never", *"complete"*}
        Specifies when mail is sent to the adress specified. See
            https://www.lrz.de/services/compute/supermuc/loadleveler/#batch
        for details.

    ``job_name'' : string, optional (default=None)
        The name of the job for the batch loader. Defaults to the basename of
        <job_dir>.

    ``job_dir'' : string, optional (default=${PWD})
        The directory containig the files for the job. Will be the working
        directory a.k.a. starting point on the node. Defaults to the current
        working directory.

    ``outfile'' : string, optional (default=None)
        The outfile to which all stdout is directed. Defaults to
        <job_dir>/<job_name>.$(schedd_host).$(jobid).out.

    ``errorfile'' : string, optional (default=None)
        The outfile to which all stderr is directed. Defaults to
        <job_dir>/<job_name>.$(schedd_host).$(jobid).out, i.e., same file for
        stdout and stderr

    ``job_type'' : string, optional ({*'parallel'*, MPICH'})
        Specifyer for parallel jobs parallelism. "parallel" for IBM mpi,
        "MPICH" for intel mpi.

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

    ``energy_policy_tag'' :  string, optional (default=None)
        The energy policy tag. For details see
            https://www.lrz.de/services/compute/supermuc/loadleveler/#energy
    ---
    Simon P. Rittmeyer (TUM), 2017
    """
    # available architectures and cpu per node (always complete node allocation)
    # this is not a complete list, but that of available clusters for project pr47fo
    _avail_arch = {'thin' :  {'classes' : ['test', 'general', 'large'],
                              'max_cpu_per_node' : 16,
                              'nodes' : {'test' : [1,32],
                                         'general' : [33,512],
                                         'large' : [513,4096]},
                             },
                    'fat' :  {'classes' : ['fattest', 'fatter', 'fat'],
                              'max_cpu_per_node' : 40,
                              'nodes' : {'fattest' : [1,4],
                                         'fatter' : [1,13],
                                         'fat' : [1,52]
                                         },
                             },
                    'phase2' :  {'classes' : ['test', 'micro', 'general', 'big'],
                                 'max_cpu_per_node' : 28,
                                 'nodes' : {'test' : [1,20],
                                            'micro' : [1,20],
                                            'general' : [21,512],
                                            'big' : [1,8],
                                            },
                                 },
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
                         'architecture' : None,
                         'job_class' : None,
                         'clean': [],
                         'email_address': None,
                         'dryrun': False,
                         'debug': True,
                         'check_consistency': True,
                         'island_count' : None,
                         'ntasks' : None,
                         'ntasks_per_node' : None,
                         'outfile': None,
                         'errorfile': None,
                         'load_modules' : [],
                         'unload_modules' : [],
                         'export_variables' : {},
                         'job_name' : None,
                         'notification' : 'complete',
                         'program' : None,
                         'job_dir' : os.path.abspath(os.getcwd()),
                         'job_type' : 'MPICH',
                         'energy_policy_tag' : None
                         }

        self.required = ['walltime',
                         'program',
                         'nnodes',
                         'architecture',
                         'job_class',
                         'email_address',
                        ]

        # let the parent do it's job, we do the explicit init here
        super(SuperMucAgent, self).__init__(init_params=True, **kwargs)

        self.loadleveler_dict = self._get_loadleveler_template()

    # add the sanity check to the parent's version
    def _init_params(self, kwargs):
        super(SuperMucAgent, self)._init_params(kwargs)
        self._check_input_sanity()
        self._expand_environment()

    def _check_input_sanity(self):
        # sanity check for the jobfolder
        # make sure there is no "~" in the jobfolder, and if so, replace it
        # with environ["HOME"]

        self.params['job_dir'] = resolve_home_work_vars(self.params['job_dir'])
        self.params['job_dir'] = os.path.abspath(self.params['job_dir'])

        if self.params['job_name'] is None:
            self.params['job_name'] = os.path.basename(self.params['job_dir'])

        # check for max lenght of loadleveler name
        #job_name = self.params['job_name']
        # if len(job_name) > 10:
            # job_name = job_name[0:10]
            # print('"job_name" variable exceeds 10 characters. Will be shortened to "{}"'.format(job_name))
            # self.params['job_name'] = job_name

        # check for the architecture
        arch = self.params['architecture'].lower()
        if arch in self._avail_arch.keys():
            self.params['architecture'] = arch
            job_class = self.params['job_class'].lower()
            if job_class not in self._avail_arch[arch]['classes']:
                raise ValueError('Architecture "{}" does not support job_class "{}"'.format(arch, job_class))
            else:
                self.params['job_class'] = job_class

        else:
            raise NotImplementedError('Support for "{}" architecture not implemented'.format(arch))

        nnodes = self.params['nnodes']
        min_nodes, max_nodes = self._avail_arch[arch]['nodes'][job_class]

        if nnodes < min_nodes or nnodes > max_nodes:
            raise ValueError('<nnodes> not in [min_nodes={}, max_nodes={}] for this "architecture" and "job_class"'.format(min_nodes, max_nodes))


        job_type = self.params['job_type']
        if not job_type in ['parallel', 'MPICH']:
            raise NotImplementedError('Unknown job_type "{}". Choose either "parallel" or "MPICH"'.format(job_type))
        elif job_type == 'MPICH':
                if not 'mpi.ibm' in self.params['unload_modules']:
                    self.params['unload_modules'] += ['mpi.ibm']
                if not 'mpi.intel' in self.params['load_modules']:
                    self.params['load_modules'] += ['mpi.intel']

        ntasks = self.params['ntasks']
        ntasks_per_node = self.params['ntasks_per_node']
        max_tasks = int(self.params['nnodes']) * self._avail_arch[self._tp_arch()]['max_cpu_per_node']

        if ntasks is None and ntasks_per_node is None:
            self.params['ntasks'] = max_tasks
        elif ntasks is not None:
            ntasks = int(ntasks)
            if ntasks_per_node is not None:
                raise ValueError('You cannot specify both, "ntasks" and "ntasks_per_node".')
            if ntasks > max_tasks:
                raise ValueError('<ntasks> > <nnodes> * max # of cpu on this architecture ({})'.format(self._tp_arch()))
            else:
                self.params['ntasks'] = int(ntasks )
        elif ntasks_per_node is not None:
            ntasks_per_node = int(ntasks_per_node)
            if ntasks_per_node > self._avail_arch[self._tp_arch()]['max_cpu_per_node']:
                raise ValueError('<ntasks_per_node> exceeds max # of cpu on this architecture ({})'.format(self._tp_arch()))
            else:
                self.params['ntasks_per_node'] = ntasks_per_node

        island_count = self.params['island_count']
        _msg = 'Specify "island_count" as list [min, max]'
        if island_count is None:
            if nnodes > 512:
                raise ValueError('Specify "island_count" if you require more than 512 nodes')
        else:
            if not job_class in ['general', 'big', 'large']:
                warnings.warn('"island_count" not required for "job_class" = "{}"'.format(job_class))
                self.params['island_count'] = None
            if not isinstance(island_count, (list, tuple)):
                raise TypeError(_msg)
            else:
                if len(island_count) !=2:
                    raise TypeError(_msg)
                if island_count[0] > island_count[1]:
                    raise ValueError(_msg)
                if island_count[1] < 2:
                    raise ValueError('Maximum island count has to be larger than >=2')

        # check for valid mail format
        check_email_address(self.params['email_address'])

        # check for paths in environment
        for key, val in self.params['export_variables'].items():
            self.params[key]=resolve_home_work_vars(val)

        self.params['program'] = resolve_home_work_vars(self.params['program'])


    # the templates
    def _tp_outfile(self):
        outfile = self.params.get('outfile')
        if outfile is None:
            outfile = os.path.join(self.params['job_dir'],
                                   '{}.$(schedd_host).$(jobid).out'.format(self.params['job_name'])
                                   )
        else:
            if not self.params['job_dir'] in outfile:
                outfile = os.path.join(self.params['job_dir'], os.path.basename(outfile))
        return outfile

    def _tp_errorfile(self):
        errfile = self.params.get('errorfile')
        if errfile is None:
            errfile = os.path.join(self.params['job_dir'],
                                   '{}.$(schedd_host).$(jobid).out'.format(self.params['job_name'])
                                    )
        else:
            if not self.params['job_dir'] in errfile:
                errfile = os.path.join(self.params['job_dir'], os.path.basename(errfile))
        return errfile

    def _tp_notification(self):
        notification = self.params['notification'].lower()
        if notification not in ['always','error','start','never','complete']:
            warnings.warn('Unknown notification mode "{}" -- fallback is "complete"'.format(notification))
            notification = 'complete'
        return notification


    def _tp_infofile(self):
        return self.params.get['infofile']

    def _tp_jobfolder(self):
        return self.params['job_dir']

    def _tp_job_name(self):
        return self.params['job_name']

    def _tp_job_type(self):
        return self.params['job_type']

    def _tp_job_class(self):
        return self.params['job_class']

    def _tp_nodeconfig(self):
        s = "#@ node = {}".format(int(self.params['nnodes']))
        ntasks = self.params['ntasks']
        ntasks_per_node = self.params['ntasks_per_node']

        #max_tasks = int(self.params['nnodes']) * self._avail_arch[self._tp_arch()]['max_cpu_per_node']

        if self.params['island_count'] is not None:
            s += "\n#@ island_count = {},{}".format(*[int(i) for i in self.params['island_count']])
        else:
            s += "\n#@ island_count = 1"

        if ntasks is not None:
            s += "\n#@ total_tasks = {}".format(ntasks)
        elif ntasks_per_node is not None:
            s += "\n#@ tasks_per_node = {}".format(ntasks_per_node)

        return s

    def _tp_arch(self):
        return self.params['architecture']

    def _tp_ncpu(self):
        nnodes = int(self.params['nnodes'])
        ntasks = self.params['ntasks']
        ntasks_per_node = self.params['ntasks_per_node']

        if ntasks is None and ntasks_per_node is None:
            return nnodes * self._avail_arch[self._tp_arch()]['max_cpu_per_node']
        elif ntasks is not None:
            return int(ntasks)
        elif ntasks_per_node is not None:
            return int(ntasks_per_node) * nnodes

    def _tp_energy(self):
        tag = self.params['energy_policy_tag']
        if tag is not None:
            return "#@ energy_policy_tag = {}\n#@ minimize_time_to_solution = yes".format(tag)
        else:
            return "#@ energy_policy_tag = NONE"

    def _tp_mpi_command(self):
        if self.params['job_type'] == 'parallel':
            return 'poe'
        else:
            return 'mpiexec'

    def _tp_email(self):
        return self.params['email_address']

    def _tp_modules(self):
        if self.params['load_modules'] or self.params['unload_modules']:
            modules = '# initialize the module system'
            modules += '\nsource /etc/profile'
            modules += '\nsource /etc/profile.d/modules.sh\n'

            modules += '\n# unloading modules'
            for m in list(self.params['unload_modules']):
                modules += '\nmodule unload {0}'.format(m)

            modules += '\n\n# loading user modules'

            for m in list(self.params['load_modules']):
                modules += '\nmodule load {0}'.format(m)
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


    def _get_loadleveler_template(self):
        """
        The LoadLeveler template string for the bash submit version.

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
        loadleveler_dict = OrderedDict()
        loadleveler_dict["LoadLeveler"] = r"""
#!/bin/bash

#-----------------------------------------------------------------------------+
# submit script written by rtools                                             |
#                                                                             |
# for details see                                                             |
#     https://www.lrz.de/services/compute/supermuc/loadleveler/               |
#                                                                             |
# Simon P. Rittmeyer (TUM), 2017                                              |
#-----------------------------------------------------------------------------+

#-----------------------------------------------------------------------------+
# LOADLEVELER CONFIGURATION                                                   |
#-----------------------------------------------------------------------------+

# job type and class
#@ job_type = {_TP_JOB_TYPE}
#@ class = {_TP_JOB_CLASS}

# specify number of tasks and node distribution
#@ node_topology = island
{_TP_NODECONFIG}

# stderr and stdout
#@ output = {_TP_OUTFILE}
#@ error = {_TP_ERRORFILE}

# starting directory a.k.a. working directory
#@ initialdir = {_TP_JOBFOLDER}

# job name
#@ job_name = {_TP_JOB_NAME}

# user config
#@ notification = {_TP_NOTIFICATION}
#@ notify_user = {_TP_EMAIL}

# energy policy
{_TP_ENERGY}

# walltime
#@ wall_clock_limit = {_TP_WALLTIME}

# from here on the job starts
#@ queue
"""[1::]

        loadleveler_dict['MODULES'] = r"""
#-----------------------------------------------------------------------------+
# THE ACTUAL JOB PROCESSING                                                   |
#-----------------------------------------------------------------------------+

echo "#--- Job started at `date`"

## modules
{_TP_MODULES}

# this one echos each command (only after module scripts!)
set -x
"""

        loadleveler_dict['ENV'] = r"""
# environment variables
{_TP_ENVIRONMENT}

# the actual binary that is run
program="{_TP_PROGRAM}"

# This one is to properly run MPI, in case required
mpi_command="{_TP_mpi_command}"
"""

        loadleveler_dict['PRE_CMD'] = r"""
# custom pre-command stuff
{_TP_PRECOMMAND}
"""

        loadleveler_dict['CMD'] = r"""
# run, Forest, run,...
{_TP_COMMAND}
"""[1::]

        loadleveler_dict['POST_CMD'] = r"""
# custom post-command stuff
{_TP_POSTCOMMAND}
"""[1::]

        loadleveler_dict['CLEAN'] = r"""
# remove the requested files
{_TP_CLEANUP}

echo "#--- Job ended at `date`"
"""[1::]

        return loadleveler_dict

    # Methods to write the files and submit the job (as well as consistency
    # checks
    def _format_loadleveler_template(self):
        """
        Return the LoadLeveler submit file string with all placeholders replaced with
        the actual values.
        """
        jobfilestring = ""
        formatdict = dict()
        for value in self.loadleveler_dict.values():
            jobfilestring += value

        keys = list([i[1] for i in Formatter().parse(jobfilestring)
                     if i[1] is not None])
        for key in keys:
            formatdict[key] = getattr(self, key.lower())()

        loadlevelerstring = jobfilestring.format(**formatdict)
        return loadlevelerstring


    def _write_loadleveler(self):
        """
        Write the actual job file. The name is determined by the PBS-name.
        """
        self._jobfilename = 'job.' + self.params['job_name'] + '.supermuc'
        jobfile = os.path.join(self.params['job_dir'], self._jobfilename)
        loadlevelerstring = self._format_loadleveler_template()
        with open(jobfile, 'w') as f:
            f.write(loadlevelerstring)

    def _submit_job(self):
        cwd = os.getcwd()
        os.chdir(self.params['job_dir'])
        job_id = None

        if self.params["dryrun"]:
            print('Prepared but not submitted (LoadLeveler title "{}")'.format(self.params['job_name']))
        else:
            out = subprocess.check_output('llsubmit {}'.format(self._jobfilename),
                                          shell=True)
            out = out.strip('\n')
            pattern =  r'llsubmit: The job "(.+)" has been submitted.'
            job_id = re.search(pattern, out).group(1)

            print('Submitted with LoadLeveler title "{}" (job id: {})'.format(self.params['job_name'], job_id))

        os.chdir(cwd)
        return job_id


    def submit(self):
        """write the loadleveler file and submit the job"""
        self._write_loadleveler()
        return self._submit_job()
