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
rtools is great!

---
Simon P. Rittmeyer
simon.rittmeyer(at)tum.de
"""

import difflib
import argparse
import numpy as np

def get_close_matches(key, all_keys, **kwargs):
    """
    Simple function that determines close matches from a given set of keys.
    This is useful for parsing user input.

    Arguments
    ---------
    ''key''
        string
        Key which should match something

    ''all_keys''
        list of strings
        All possible values that ``key'' can take.

    Returns
    -------
    ''alternatives''
        string
        Formatted IO string with close matches.
    """
    similars = difflib.get_close_matches(key, all_keys, **kwargs)
    if len(similars) > 0:
        alternatives = 'You probably tried one of these:'
        for i in similars:
            alternatives += '\n\t{}'.format(i)
    else:
        alternatives = ''

    return alternatives


def get_cmd_parser():
    """
    Generic command line parser based on the argparse module.

    Arguments
    ---------
    None

    Returns
    -------
    Parser. Upon calling parser.parse_args() this parser will return a Namespace.
    This namespace contains the following boolean variables:
        * read
        * update
        * send
        * analyze
        * check
        * show
        * clean
        * build
        * install
        * test
        * prepare
        * calculate
        * ...
    By default, all variables are `False`, but they are stored `True` upon
    calling the respective option from the command line.
    """

    parser = argparse.ArgumentParser(description='Generic command line parser from rtools')

    parser.add_argument('--read',
                        action = 'store_true',
                        default = False,
                        help = "Read.")
    parser.add_argument('--update',
                        action = 'store_true',
                        default = False,
                        help = "Update.")
    parser.add_argument('--send',
                        action = 'store_true',
                        default = False,
                        help = "Send.")
    parser.add_argument('--resend',
                        action = 'store_true',
                        default = False,
                        help = "Resend.")
    parser.add_argument('--analyze',
                        action = 'store_true',
                        default = False,
                        help = "Analyze.")
    parser.add_argument('--write',
                        action = 'store_true',
                        default = False,
                        help = "Write.")
    parser.add_argument('--check',
                        action = 'store_true',
                        default = False,
                        help = "Check.")
    parser.add_argument('--show',
                        action = 'store_true',
                        default = False,
                        help = "Show.")
    parser.add_argument('--clean',
                        action = 'store_true',
                        default = False,
                        help = "Clean.")
    parser.add_argument('--build',
                        action = 'store_true',
                        default = False,
                        help = "Build.")
    parser.add_argument('--install',
                        action = 'store_true',
                        default = False,
                        help = "Install.")
    parser.add_argument('--export',
                        action = 'store_true',
                        default = False,
                        help = "Export.")
    parser.add_argument('--test',
                        action = 'store_true',
                        default = False,
                        help = "Test.")
    parser.add_argument('--calculate',
                        action = 'store_true',
                        default = False,
                        help = "Calculate.")
    parser.add_argument('--render',
                        action = 'store_true',
                        default = False,
                        help = "Render.")
    parser.add_argument('--prepare',
                        action = 'store_true',
                        default = False,
                        help = "Prepare.")
    parser.add_argument('--extend',
                        action = 'store_true',
                        default = False,
                        help = "Extend.")
    parser.add_argument('--ncpu',
                        type=int,
                        default = 1,
                        help = "Number of cores")
    parser.add_argument('--system',
                        type=str,
                        default='',
                        help='System')
    parser.add_argument('--pseudopotential',
                        type=str,
                        default='',
                        help='Pseudopotential')
    parser.add_argument('--cutoff',
                        action='store_true',
                        default=False,
                        help='Cutoff')
    parser.add_argument('--kpoints',
                        action='store_true',
                        default=False,
                        help='Kpoints')
    parser.add_argument('--fatnodes',
                        action='store_true',
                        default=False,
                        help='fatnodes')

    return parser


def get_cmd_args():
    """
    Wrapper to automatically run parse_args() on the parser from
    get_cmd_parser()
    """
    parser = get_cmd_parser()
    args = parser.parse_args()
    return args


def format_timing(start, stop, fmt = '{0:02d}h {1:02d}m {2:02d}s'):
    """
    Return a formatted time difference. There is no conversion from hours to
    days.

    Parameters
    ----------
    ''start''
        string
        start time as obtained from time.time()

    ''stop''
        string
        stop time as obtained from time.time()

    ''fmt''
        string, optional (default = '{02d}h {02d}m {02d}s')
        Template for the output string. It must be compatibe with the (hours,
        minutes, seconds) tuple.

    Returns
    -------
    Formatted string
    """
    runtime=int(round(stop-start))
    h = runtime / int(3600) # hours
    runtime = runtime % 3600 # remaining seconds
    m = runtime / 60 # minutes
    s = runtime % 60 # seconds
    return fmt.format(*[int(i) for i in (h,m,s)])

def print_histogram(hist, bin_edges):
    """
    Small function to visualize the output of numpy's histogram function on the
    command line. Just pass the output of numpy.histogram as arguments and
    you're done.

    Parameters
    ----------
    hist: (Nbins,) array
        The histogram values

    bin_edges: (Nbins+1,) array
        The bin edges.

    Returns
    -------
    None
    """
    Nbins=len(bin_edges)-1

    # the maximum should correspond to 50+1 indicators
    indicator = '#'
    imax = 50

    scale = imax / float(np.max(hist))

    print('-'*80)
    print('HISTOGRAM')
    print('-'*80)
    print('{:+06.3f}'.format(bin_edges[0]))
    for i in np.arange(Nbins):
        print('\t' + indicator*int(scale*hist[i]+1) + ' {:<10.2f}'.format(hist[i]))
        print('{:+06.3f}'.format(bin_edges[i+1]))

def iceil(num, den):
    """
    Small function to calculate the ceiling of the division of
    two integer values only using integer arithmetic.

    Parameters
    ----------
    num: int
        The numerator

    den: int
        The denominator

    Returns
    -------
    int
    """
    #if den < 0:
    #    return (num + (den + 1)) // den
    #else:
    #    return (num + (den - 1)) // den
    # The following formula is equivalent but easily parallelizable:
    return (num - den // abs(den)) // den + 1

