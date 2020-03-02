import os
import unittest
import shutil
import tempfile
from rtools.submitagents.workstation import castep, WorkstationAgent

try:
    from rtools.filesys import which
    castep_installed = True
    program = 'castep'
    if not which(program):
        castep_installed = False
    else:
        castep_installed = True
except ImportError:
    castep_installed = False

class TestBaseArthurAgent(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)

    def test_check_arg_works_for_nonexisting_arg(self):
        with self.assertRaises(RuntimeError):
            WorkstationAgent(job_dir=self.tmpdir, pbsnamee='myjob')

class TestCastepAgent(unittest.TestCase):
    """
    Test if the setup of the CASTEP agent works as expected.
    """
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.seed = 'h2o_test'

        self.cellfile_path = os.path.join(self.tmpdir, self.seed + '.cell')
        self.paramfile_path = os.path.join(self.tmpdir, self.seed + '.param')

    def test_castep_agent_with_missing_seed(self):
        with self.assertRaises(ValueError):
            R = castep.Castep(job_dir=self.tmpdir,
                              dryrun=True,
                              ignore_defaultfile=True,
                              program='castep',
                              check_consistency=False)
            R.submit()


    def test_castep_agent_with_dryrun(self):
        R = castep.Castep(job_dir=self.tmpdir,
                          seed=self.seed,
                          ignore_defaultfile=True,
                          dryrun=True,
                          program='castep',
                          check_consistency=False)

        R._write_bash()
        R.submit()

        jobfile = os.path.isfile(os.path.join(
            self.tmpdir,
            'job.'+self.seed+'.sh'))
        self.assertTrue(jobfile)

    @unittest.skipIf(not castep_installed, 'castep not installed, skipping test')
    def test_castep_consistency_check_with_files(self):
        open(self.cellfile_path, 'w').close()
        with open(self.paramfile_path, 'w') as f:
            f.write('run_time')

        R = castep.Castep(job_dir=self.tmpdir,
                          seed=self.seed,
                          dryrun=True,
                          program='castep',
                          ignore_defaultfile=True,
                          check_consistency=True)
        R.submit()

    def test_castep_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = castep.Castep(job_dir=self.tmpdir,
                              seed=self.seed,
                              ignore_defaultfile=True,
                              dryrun=True,
                              program='castep',
                              check_consistency=True)
            R.submit()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()


