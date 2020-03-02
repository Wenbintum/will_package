#!/usr/bin/env python

import os
import unittest
import shutil
import tempfile
from rtools.submitagents.supermuc import SuperMucAgent
from rtools.submitagents.supermuc import pythonscript
from rtools.submitagents.supermuc import castep
from rtools.submitagents.supermuc import aims

class TestSuperMucAgent(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'job_class' : 'fattest',
                'architecture' : 'fat',
                'program' : 'dummy',
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.required['job_dir'] = self.tmpdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_check_arg_works_for_nonexisting_arg(self):
        with self.assertRaises(RuntimeError):
            SuperMucAgent(pbsname='myjob', **self.required)

    def check_complete_input(self):
        SuperMucAgent(**self.required)

    def test_check_inconsistent_input(self):
        required = self.required.copy()

        required['nnodes'] = 5
        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        required['job_class'] = 'general'

        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        required['architecture'] = 'phase2'

        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        # too many nodes
        required['nnodes'] = 514

        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        # no island count
        required['architecture'] = 'thin'
        required['job_class'] = 'large'
        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        # wrong format for island_count
        required['island_count'] = 1
        with self.assertRaises(TypeError):
            SuperMucAgent(**required)

        required['island_count'] = [1]
        with self.assertRaises(TypeError):
            SuperMucAgent(**required)

        required['island_count'] = [2,1]
        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        required['island_count'] = [1,2]
        SuperMucAgent(**required)

    def test_check_incomplete_input(self):
        required = self.required.copy()

        required['walltime'] = None

        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

        required.pop('walltime')
        with self.assertRaises(ValueError):
            SuperMucAgent(**required)

    def test_mpichange(self):
        required = self.required.copy()
        required['job_type'] = 'mpich'
        with self.assertRaises(NotImplementedError):
            SuperMucAgent(**required)

        required['job_type'] = 'MPICH'
        Agent=SuperMucAgent(**required)

        self.assertTrue('mpi.intel' in Agent.params['load_modules'])
        self.assertTrue('mpi.ibm' in Agent.params['unload_modules'])

    def test_ncpu(self):
        Agent = SuperMucAgent(**self.required)
        self.assertEquals(2*40, Agent._tp_ncpu())

    def test_wrong_cluster(self):
        required = self.required.copy()
        required['architecture'] = 'thiiin'
        with self.assertRaises(NotImplementedError):
            Agent = SuperMucAgent(**required)

    def test_invalid_mail(self):
        required = self.required.copy()

        # this should work
        Agent = SuperMucAgent(**required)

        # just some examples, feel fre to add more
        invalids = ['a @b.c',
                    'a%b',
                    'ab',
                    'a(at)b.c',
                    ]

        for i in invalids:
            required['email_address'] = i
            with self.assertRaises(RuntimeError):
                Agent = SuperMucAgent(**required)


    def test_write(self):
        # this should work
        Agent = SuperMucAgent(**self.required)
        Agent._write_loadleveler()


class TestPythonScriptAgent(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
    required = {'walltime' : '100:00:00',
                'program' : 'dummy',
                'pythonpath' : 'here',
                'dryrun' : True,
                'pyscript' : 'dummy.py',
                'nnodes' : 2,
                'job_class' : 'fattest',
                'architecture' : 'fat',
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        self.required['job_dir'] = self.tmpdir

    # def tearDown(self):
        # shutil.rmtree(self.tmpdir)

    def test_write(self):
        # this should work
        Agent = pythonscript.PythonScriptAgent(**self.required)
        Agent._write_loadleveler()

    def test_submit(self):
        # this should work
        Agent = pythonscript.PythonScriptAgent(**self.required)
        Agent.submit()

class TestCastepAgent(unittest.TestCase):
    """
    Test if the setup of the CASTEP agent works as expected.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'architecture' : 'fat',
                'job_class' : 'fattest',
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
            R = castep.Castep(job_dir=self.tmpdir,
                                  check_consistency=False,
                                  **kwargs)
            R.submit()

    def test_castep_agent_with_dryrun(self):
        kwargs = self.required.copy()
        kwargs['seed'] = 'myjob2'
        R = castep.Castep(job_dir=self.tmpdir,
                              check_consistency=False,
                              **kwargs)
        R.submit()
        supermucfile = os.path.isfile(os.path.join(self.tmpdir,
            'job.'+kwargs['seed']+'.supermuc'))

        self.assertTrue(supermucfile)

    def test_castep_consistency_check_with_files(self):
        cellfile_path = os.path.join(self.tmpdir, self.required['seed'] + '.cell')
        paramfile_path = os.path.join(self.tmpdir, self.required['seed'] + '.param')

        open(cellfile_path, 'w').close()
        with open(paramfile_path, 'w') as f:
            f.write('run_time')

        R = castep.Castep(job_dir=self.tmpdir,
                              check_consistency=False,
                              **self.required)
        R.submit()

    def test_castep_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = castep.Castep(job_dir=self.tmpdir,
                                  check_consistency=True,
                                  **self.required)
            R.submit()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class TestAimsAgent(unittest.TestCase):
    """
    Test if the setup of the FHIaims agent works as expected.
    """
    required = {'walltime' : '100:00:00',
                'nnodes' : 2,
                'architecture' : 'fat',
                'job_class' : 'fattest',
                'program' : 'dummy',
                'dryrun' : True,
                'job_name' : 'aimsrun',
                'email_address' : 'a@b.c'}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.foldername = os.path.basename(self.tmpdir)
        print(self.tmpdir)

    def test_aims_agent_aimsout(self):
        kwargs = self.required.copy()
        kwargs['job_name'] = 'aimsout'
        aimsout = 'aims.out'
        R = aims.Aims(job_dir=self.tmpdir,
                      check_consistency=False,
                      aims_outfile = aimsout,
                      **kwargs)
        self.assertEquals(R._tp_aimsout(), aimsout)

    def test_aims_agent_with_dryrun(self):
        kwargs = self.required.copy()
        kwargs['job_name'] = 'writefiles'
        R = aims.Aims(job_dir=self.tmpdir,
                      check_consistency=False,
                      **kwargs)
        R.submit()
        supermucfile = os.path.isfile(os.path.join(self.tmpdir,
            'job.'+kwargs['job_name']+'.supermuc'))

        self.assertTrue(supermucfile)

    def test_aims_consistency_check_with_files(self):
        geomfile_path = os.path.join(self.tmpdir, 'geometry.in')
        controlfile_path = os.path.join(self.tmpdir, 'control.in')

        open(geomfile_path, 'w').close()
        with open(controlfile_path, 'w') as f:
            f.write('walltime')

        kwargs = self.required.copy()
        kwargs['job_name'] = 'consistency'
        kwargs['program'] = 'ls'

        R = aims.Aims(job_dir=self.tmpdir,
                      check_consistency=True,
                      **kwargs)
        R.submit()

    def test_aims_consistency_check_with_files_adds_walltime(self):
        geomfile_path = os.path.join(self.tmpdir, 'geometry.in')
        controlfile_path = os.path.join(self.tmpdir, 'control.in')

        open(geomfile_path, 'w').close()
        open(controlfile_path, 'w').close()

        kwargs = self.required.copy()
        kwargs['job_name'] = 'consistency_walltime'
        kwargs['program'] = 'ls'

        R = aims.Aims(job_dir=self.tmpdir,
                      check_consistency=True,
                      **kwargs)
        R.submit()

        walltime = False
        print(controlfile_path)
        for line in open(controlfile_path, 'r'):
            if 'walltime' in line:
                walltime = True
                break
        self.assertTrue(walltime)


    def test_aims_consistency_check_raises_warning(self):
        with self.assertRaises(Warning):
            R = aims.Aims(job_dir=self.tmpdir,
                                  check_consistency=True,
                                  **self.required)
            R.submit()

    # def tearDown(self):
        # shutil.rmtree(self.tmpdir)

if __name__ == '__main__':
    unittest.main()
