import os
import unittest
import shutil
import tempfile
from rtools.submitagents.lrzlinuxcluster import LinuxClusterAgent
from rtools.submitagents.lrzlinuxcluster import pythonscript
from rtools.submitagents.lrzlinuxcluster import castep as lrz_castep

class TestBaseLinuxClusterAgent(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'clusters' : 'mpp2',
                'program' : 'dummy',
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.required['job_dir'] = self.tmpdir

    def test_check_arg_works_for_nonexisting_arg(self):
        with self.assertRaises(RuntimeError):
            LinuxClusterAgent(pbsname='myjob', **self.required)

    def check_complete_input(self):
        LinuxClusterAgent(**self.required)

    def test_check_incomplete_input(self):
        required = self.required.copy()

        required['walltime'] = None

        with self.assertRaises(ValueError):
            LinuxClusterAgent(**required)

        required.pop('walltime')
        with self.assertRaises(ValueError):
            LinuxClusterAgent(**required)

    def test_env_replacement(self):
        checkstr = '349853894547395843754398'
        Agent = LinuxClusterAgent(slurmname = checkstr,
                                  **self.required)

        self.assertEqual(Agent._tp_slurmname(), checkstr[0:10])

    def test_ncpu(self):
        Agent = LinuxClusterAgent(**self.required)
        self.assertEquals(2*28, Agent._tp_ncpu())

    def test_wrong_cluster(self):
        required = self.required.copy()
        required['clusters'] = 'mppp3'
        with self.assertRaises(NotImplementedError):
            Agent = LinuxClusterAgent(**required)

    def test_invalid_mail(self):
        required = self.required.copy()

        # this should work
        Agent = LinuxClusterAgent(**required)

        # just some examples, feel fre to add more
        invalids = ['a @b.c',
                    'a%b',
                    'ab',
                    'a(at)b.c',
                    ]

        for i in invalids:
            required['email_address'] = i
            with self.assertRaises(RuntimeError):
                Agent = LinuxClusterAgent(**required)


    def test_write(self):
        # this should work
        Agent = LinuxClusterAgent(**self.required)
        Agent._write_slurm()


class TestPythonScriptAgent(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'clusters' : 'mpp2',
                'program' : 'dummy',
                'pythonpath' : 'here',
                'dryrun' : True,
                'pyscript' : 'dummy.py',
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.required['job_dir'] = self.tmpdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_write(self):
        # this should work
        Agent = pythonscript.PythonScriptAgent(**self.required)
        Agent._write_slurm()

    def test_submit(self):
        # this should work
        Agent = pythonscript.PythonScriptAgent(**self.required)
        Agent.submit()

class TestLRZCastepAgent(unittest.TestCase):
    """
    Test if the setup of the CASTEP agent works as expected.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'clusters' : 'mpp2',
                'program' : 'dummy',
                'seed' : 'test',
                'pp_dir' : '.',
                'dryrun' : True,
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)

    def test_castep_agent_with_missing_seed(self):
        kwargs = self.required.copy()
        kwargs.pop('seed')
        with self.assertRaises(ValueError):
            R = lrz_castep.Castep(job_dir=self.tmpdir,
                                  check_consistency=False,
                                  ignore_defaultfile=True,
                                  **kwargs)
            R.submit()

    def test_castep_agent_with_dryrun(self):
        kwargs = self.required.copy()
        kwargs['seed'] = 'myjob2'
        R = lrz_castep.Castep(job_dir=self.tmpdir,
                              check_consistency=False,
                              ignore_defaultfile=True,
                              **kwargs)
        R.submit()
        slurmfile = os.path.isfile(os.path.join(self.tmpdir,
            'job.'+kwargs['seed']+'.linuxcluster'))

        self.assertTrue(slurmfile)

    def test_castep_consistency_check_with_files(self):
        cellfile_path = os.path.join(self.tmpdir, self.required['seed'] + '.cell')
        paramfile_path = os.path.join(self.tmpdir, self.required['seed'] + '.param')

        open(cellfile_path, 'w').close()
        with open(paramfile_path, 'w') as f:
            f.write('run_time')

        R = lrz_castep.Castep(job_dir=self.tmpdir,
                              check_consistency=False,
                              ignore_defaultfile=True,
                              **self.required)
        R.submit()

    def test_castep_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = lrz_castep.Castep(job_dir=self.tmpdir,
                                  check_consistency=True,
                                  ignore_defaultfile=True,
                                  **self.required)
            R.submit()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

if __name__ == '__main__':
    unittest.main()
