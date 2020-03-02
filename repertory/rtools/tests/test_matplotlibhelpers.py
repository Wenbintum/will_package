#!/usr/bin/env python
import unittest
import tempfile
import numpy as np
import os
import shutil

import matplotlib
matplotlib.use('Agg')

from rtools.helpers import matplotlibhelpers as hlp
import matplotlib.pyplot as plt
from matplotlib import rcParams

class TestMatplotlibHelpers(unittest.TestCase):
    """
    Test some functionality of the base agent class.
    """
#     @classmethod
#     def setUpClass(self):
#         self.tmpdir = tempfile.mkdtemp()
#         self.foldername = os.path.basename(self.tmpdir)

#     @classmethod
#     def tearDownClass(self):
#         try:
#             shutil.rmtree(self.foldername)
#         except IOError:
#             pass

    def plot(self):
        x = np.linspace(0, 2*np.pi)
        y = np.sin(x)
        plt.plot(x,y)

    def label(self):
        plt.xlabel('coordinate $x$')
        plt.ylabel('function $y=\sin(x)$')

    def test_defaults(self):
        plt.clf()
        hlp.set_defaults(rcParams)
        self.plot()
        self.label()
        plt.draw()

    def test_latex(self):
        plt.clf()
        hlp.set_latex(rcParams)
        self.plot()
        self.label()
        plt.draw()

    def test_mathtext(self):
        plt.clf()
        hlp.set_mathtext(rcParams)
        self.plot()
        self.label()
        plt.draw()

#     def test_write(self):
#         plt.clf()
#         self.test_mathtext()
#         hlp.write('test', folder=self.foldername, write_pdf=True)
#         hlp.write('test', folder=self.foldername, write_png=True)
#         hlp.write('test', folder=self.foldername, write_eps=True)
#         hlp.write('test', folder=self.foldername, write_pdfviaeps=True)
#         hlp.write('test', folder=self.foldername, write_pngviaeps=True)

if __name__ == '__main__':
    unittest.main()
