rtools
======

## bundling generic coding efforts in rtools

Welcome to the rtools project!

### What's this thing called rtools?
Idea (~2014): collect generic tools and routines written in our group in order
to avoid re-inventing the wheel over and over again 
              
``rtools`` is organized as python (2.7.X) module incl. executable scripts

- submit agents to arthur, linux cluster, local machines, (supermuc is work in progress)
- TUM CD color definitions (ready-to-use palettes for keynote, gimp, inkscape, matplotlib, LaTeX,
scribus...)
- cube file routines (read/write/add/subtract/multiply/cut) -> ase.io.cube module
- framework for automatized convergence tests and PES/anything mapping
- dozens of further helper routines, prominently matplotlibhelpers (setup, fonts, colormaps,...)

### Installation
A detailed tutorial is available in our TheoChemWiki: https://wiki.tum.de/display/theochem/rtools

#### Quick installation (for the impatient)

```bash
git clone git@gitlab.lrz.de:theochem/rtools.git
cd rtools
python setup.py install --user
# done
# (optional) run the tests
nosetest tests
```

### API Reference
The API reference gives you all the details on what is available and how to use it. For a (hopefully) up-to-date version, http://rtools (only available in our local network).

You can always compile the documentation on your own.

```bash
# make sure sphinx is installed
sudo apt-get install python-sphinx

cd rtools/docs
make html
chromium _build/html/index.html
```

Or, if you are running on MacOSX using `macports`

```bash
# make sure sphinx is installed
sudo port install py27-sphinx py27-numpydoc

cd rtools/docs
make html
open _build/html/index.html
```

### Contribute
If you want to contribute to rtools, we propose the same workflow as also suggested for [ase](https://wiki.fysik.dtu.dk/ase/development/contribute.html#).
In general this means

* Never work in master branch locally or on GitLab.
* Make a new branch for whatever you are doing. When you are done, push it to your own repository and make a merge request from that branch in your repository to official master.


As it comes to commit messages, please follow [numpy's guidelines](http://docs.scipy.org/doc/numpy/dev/gitwash/development_workflow.html)
which in particular require to start commit messages with an appropriate acronym:

```
API: an (incompatible) API change
BLD: change related to building numpy
BUG: bug fix
DEP: deprecate something, or remove a deprecated object
DEV: development tool or utility
DOC: documentation
ENH: enhancement
MAINT: maintenance commit (refactoring, typos, etc.)
REV: revert an earlier commit
STY: style fix (whitespace, PEP8)
TST: addition or modification of tests
```
