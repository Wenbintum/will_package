#!/usr/bin/env python
import unittest
import time
import os
import multiprocessing
try:
    from rtools.filesys.lockfile import open_locked
    lockfile_installed = True
except (ImportError, RuntimeError):
    lockfile_installed = False

from collections import Counter

@unittest.skipIf(not lockfile_installed, "Skipped")
class TestRaceCondition(unittest.TestCase):
    def setUp(self):
        self.filename = "race_test.txt"
        self.jobs = list()
        self.loops = 100
        self.processes = 10
        self.separator = "s"

    def tearDown(self):
        try:
            #pass
            os.remove(self.filename)
        except IOError:
            raise

    def worker(self, filename, num):
        with open_locked(filename, "a") as f:
            for i in range(self.loops):
                f.write(str(num))
            f.write(self.separator)

    def test_race(self):
        for i in range(self.processes):
            p = multiprocessing.Process(target=self.worker, args=(self.filename, i,))
            p.start()
            p.join()

        with open(self.filename, "r") as f:
            data = f.readline()
            groups = Counter(data.split(self.separator))
            self.assertTrue(any(groups.values()) == 1)

if __name__ == '__main__':
    unittest.main()

