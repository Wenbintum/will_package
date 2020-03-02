#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages
from rtools import __version__
import os
import platform

import sys
if sys.version_info < (2, 7):
    sys.exit('Sorry, Python < 2.7 is not supported. Really not.')


cwd = os.getcwd()


# platform test for the local debian image
if 'debian-8.' in platform.platform():
    print("""
    Sorry, as long as our jessie images are not upgraded, this will kill your python installation.
    As a hot-fix, please run

        echo "export PYTHONPATH=${PWD}/rtools:\$PYTHONPATH" >> ~/.bashrc
        source ~/.bashrc
    """[1:])

    exit()


setup(
    name="rtools",
    version=__version__,
    description="Collection of useful python/LaTex/... tools",
    author="Reuter Group at TUM",
    maintainer="Simon P. Rittmeyer <simon.rittmeyer@tum.de>,\
Christoph Schober <christoph.schober@ch.tum.de>",
    author_email="simon.rittmeyer@tum.de",
    url="https://gitlab.lrz.de/theochem/rtools.git",
    packages=find_packages(),
    # setup_requires is for some packages such as tables which do not
    # explicitely add numpy to their dependencies to encourage the user
    # to use optimized system-wide installation using their systems'
    # package manager (e.g. apt-get or similar). Add it here for the
    # cases where system numpy is not available, e.g. clean virtualenvs.
    setup_requires=['numpy'],
    # install_requires are all external packages required by the core
    # rtools modules to work. All of these dependencies are available
    # from the Python Package Index using pip
    install_requires=['numpy',
                      'scipy',
                      #'ase',
                      #'lxml',
                      'matplotlib',
                      #'pandas',
                      'setuptools',
                      #'sqlalchemy',
                      #'tables',
                      ],
    # specify any more special dependencies (e.g. not pip-installable)
    # that are only used for certain features of rtools
    extras_require={'cheminformatics': ["rdkit", "openbabel"]},
    license='GPLv3',
    scripts=['scripts/aims_memtrace.py',
             'scripts/ConvertStructure',
             'scripts/CastepInterlayerDist',
             'scripts/get_compute_nodes.py',
             'scripts/menu',
             'scripts/myq',
             'scripts/Rename',
             'scripts/Path2tick',
             'scripts/SyncDaemon',
             'scripts/ShowColors',
             'scripts/ProfilePython',
             'scripts/SubmitAims',
             'scripts/SubmitCastep',
             'scripts/SubmitGeneric',
             'scripts/SubmitPython',
             'scripts/SubmitSuper',
             'scripts/cube_tools/CubeAdd',
             'scripts/cube_tools/CubeInfo',
             'scripts/cube_tools/CubeMultiply',
             'scripts/cube_tools/CubeRead',
             'scripts/cube_tools/CubeSubtract',
             'scripts/compile_scripts/CASTEP/make_castep_LRZ.sh',
             'scripts/compile_scripts/CASTEP/make_castep_locally.sh',
             'scripts/compile_scripts/CASTEP/test_castep_LRZ.sh',
             'scripts/compile_scripts/CASTEP/test_castep_locally.sh',
             'scripts/compile_scripts/OpenBlas/OpenBLAS-quickbuild-ifort-x86_64-portable.sh',
             'scripts/compile_scripts/OpenBlas/README.info'
             ])
