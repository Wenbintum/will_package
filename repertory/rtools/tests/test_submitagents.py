import os
import unittest
import shutil
import tempfile
from rtools.submitagents.arthur import castep, aims, ArthurAgent

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
            ArthurAgent(job_dir=self.tmpdir, pbsnamee='myjob', exclude_nodes=['tick1', 'tick2'])

class TestCastepAgent(unittest.TestCase):
    """
    Test if the setup of the CASTEP agent works as expected.
    """
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.foldername = 'test'
        self.seed = 'h2o_test'
        self.pbsname = 'testing_agent'

        self.cellfile_path = os.path.join(self.tmpdir, self.seed + '.cell')
        self.paramfile_path = os.path.join(self.tmpdir, self.seed + '.param')

    def test_castep_agent_with_missing_seed(self):
        with self.assertRaises(ValueError):
            R = castep.Castep(job_dir=self.tmpdir,
                              dryrun=True,
                              program='castep',
                              ignore_defaultfile=True,
                              check_consistency=False)
            R.submit()

    def test_castep_agent_email(self):
        R = castep.Castep(job_dir=self.tmpdir,
                          seed=self.seed,
                          dryrun=True,
                          email_address = 'r@too.ls',
                          ignore_defaultfile=True,
                          program='castep',
                          check_consistency=False)

        self.assertTrue(R._tp_email_address(), 'r@too.ls')

    def test_castep_agent_with_dryrun(self):
        R = castep.Castep(job_dir=self.tmpdir,
                          seed=self.seed,
                          dryrun=True,
                          ignore_defaultfile=True,
                          program='castep',
                          check_consistency=False)

        R.submit()

        pbsfile = os.path.isfile(os.path.join(
            self.tmpdir,
            'job.'+self.seed+'.arthur'))
        self.assertTrue(pbsfile)

    @unittest.skipIf(not castep_installed, 'castep not installed, skipping test')
    def test_castep_consistency_check_with_files(self):
        open(self.cellfile_path, 'w').close()
        with open(self.paramfile_path, 'w') as f:
            f.write('run_time')

        R = castep.Castep(job_dir=self.tmpdir,
                          seed=self.seed,
                          dryrun=True,
                          ignore_defaultfile=True,
                          exclude_nodes=['tick1', 'tick4'],
                          program='castep',
                          check_consistency=True)
        R.submit()

    def test_castep_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = castep.Castep(job_dir=self.tmpdir,
                              seed=self.seed,
                              dryrun=True,
                              ignore_defaultfile=True,
                              program='castep',
                              check_consistency=True)
            R.submit()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class TestAimsAgent(unittest.TestCase):
    """
    Test if the setup of the AIMS agent works as expected.
    """
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.pbsname = 'testing_agent'

        self.control_path = os.path.join(self.tmpdir, 'control.in')
        self.geometry_path = os.path.join(self.tmpdir, 'geometry.in')

    def test_aims_without_pbsname(self):
        R = aims.Aims(job_dir=self.tmpdir,
                      dryrun=True,
                      program='aims',
                      check_consistency=False)
        R.submit()
        pbsfile = os.path.isfile(os.path.join(
            self.tmpdir,
            'job.'+self.foldername+'.arthur'))
        self.assertTrue(pbsfile)

    def test_aims_with_dryrun(self):
        R = aims.Aims(job_dir=self.tmpdir,
                      program='aims',
                      pbsname=self.pbsname,
                      dryrun=True,
                      check_consistency=False)
        R.submit()
        pbsfile = os.path.isfile(os.path.join(
            self.tmpdir,
            'job.'+self.pbsname+'.arthur'))
        self.assertTrue(pbsfile)

    def test_aims_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = aims.Aims(job_dir=self.tmpdir,
                          program='aims',
                          dryrun=True,
                          pbsname=self.pbsname,
                          check_consistency=True)
            R.submit()

    def test_aims_consistency_check_with_files(self):
        open(self.control_path, 'w').close()
        open(self.geometry_path, 'w').close()
        R = aims.Aims(job_dir=self.tmpdir,
                      dryrun=True,
                      program='aims',
                      pbsname=self.pbsname,
                      check_consistency=True)
        R.submit()

    def test_aims_consistency_check_with_files_adds_walltime(self):

        open(self.geometry_path, 'w').close()
        open(self.control_path, 'w').close()

        R = aims.Aims(job_dir=self.tmpdir,
                      dryrun=True,
                      program='aims',
                      pbsname=self.pbsname,
                      check_consistency=True)
        R.submit()

        walltime = False
        for line in open(self.control_path, 'r'):
            if 'walltime' in line:
                walltime = True
                break
        self.assertTrue(walltime)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)




if __name__ == '__main__':
    unittest.main()


