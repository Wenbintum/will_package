.. rtools documentation master file, created by
   sphinx-quickstart on Tue Jul 29 15:53:57 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to rtools's documentation!
==================================

The following pages collect documentation for various tools and scripts. If you want to add scripts or documentation, feel free to do so. 

Installation
============

There are detailed installation tutorials available on the rtools-page in the TheoChem wiki: https://wiki.tum.de/display/theochem/rtools. 

Quick installation
------------------

.. code-block:: bash

    # in the top-level rtools directory
    python setup.py install --user
    # optional, run the tests:
    nosetests tests
    # Done.

Contribute
==========

For more information on how to contribute, please visit the rtools-page in the TheoChem wiki: https://wiki.tum.de/display/theochem/rtools


Documentation
=============

Find more information on how to write documentation: http://sphinx-doc.org/tutorial.html

Contents:

.. toctree::
   :maxdepth: 2

   docstrings.rst

   rtools.rst

   scripts.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

