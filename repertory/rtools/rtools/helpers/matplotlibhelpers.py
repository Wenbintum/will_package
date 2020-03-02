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
-----------------
MatplotlibHelpers
-----------------

Features
--------
    * ``tumcolors`` dictionary with colors from the TUM CD styleguide, use
      show_colors() to visualize
    * ``latex_geo`` dictionary with textwidth and -height measures (in mm) as
      defined in the KOMA classes for A4 paper
    * set_defaults() function for default settings
    * set_latex() function for actual true LaTeX rendering
    * set_mathtext() function for convenient mathtext rendering
    * write() function for convenient output creation
    * create_cmap() function to create custom colormaps

Minimal Working Example:
------------------------
This example is supposed to clarify the workflow when using matplotlibhelpers::

    #!/usr/bin/env python

    # Flag that triggers latex rendering
    #latex = False
    latex = True

    # # # # # # # # # # #
    # plotting in general
    # # # # # # # # # # #

    # matplotlib tools
    import matplotlib.pyplot as plt
    from   matplotlib import rcParams

    # numpy
    import numpy as np

    # matplotlib helpers
    import rtools.helpers.matplotlibhelpers as helpers
    from rtools.helpers.matplotlibhelpers import tumcolors as colors


    # set some defaults from Matplotlibhelpers
    helpers.set_defaults(rcParams)

    # Set the font
    if latex:
        helpers.set_latex(rcParams, font = 'helvetica')
    else:
        helpers.set_mathtext(rcParams, family = 'sans-serif')

    # helpers defines a ``width`` which corresponds to the textwidth in LaTeX
    # KOMA-class documents with DIV=10
    width = helpers.width
    height = width / (1.5*helpers.golden_ratio)

    # Set the size of the figure
    rcParams['figure.figsize'] = (width, height) # x,y

    # further plot parameters
    # see: http://matplotlib.org/users/customizing.html#matplotlibrc-sample
    # the left side of the subplots of the figure
    rcParams['figure.subplot.left']   = 0.11

    # the right side of the subplots of the figure
    rcParams['figure.subplot.right']  = 0.95

    # the bottom of the subplots of the figure
    rcParams['figure.subplot.bottom'] = 0.18

    # the top of the subplots of the figure
    rcParams['figure.subplot.top']    = 0.97

    # the amount of width reserved for blank space between subplots
    rcParams['figure.subplot.hspace'] = 0.6

    # the amount of height reserved for white space between subplots
    rcParams['figure.subplot.wspace'] = 0.6
    #---------------------------------------------------------------------------
    #
    # HERE GOES YOUR PLOTTING
    # AND FURTHER FORMATTING
    #
    #---------------------------------------------------------------------------

    # writing the plot
    filename = 'myplot'

    # PDF output by default
    helpers.write(filename)


---
Simon P. Rittmeyer, 2013-2015
simon.rittmeyer(at)tum.de
"""


import os
import subprocess
import matplotlib
import matplotlib.pyplot as plt
from time import strftime

import numpy as np
from rtools import tumcd
from rtools.tumcd.tumcolors import TUMcolors

# ----------
# TUM COLORS
# ----------
__tumcolors_obj = TUMcolors()
tumcolors = __tumcolors_obj.export_matplotlib()

# convenience wrapper
def show_colors():
    __tumcolors_obj.show_colors()


def create_cmap(start, end, mid = None, N = 256, extend = 'neither',
                over = None, under = None, normalize = None):
    """
    Function that creates matplotlib colormaps. Note that input colors must
    be RGB tuples within [0,1].

    Parameters
    ----------
    start : 3-tuple
        RGB-Tuple defining the start color of the color map.

    end : 3-tuple
      RGB-Tuple defining the end color of the color map.

    mid : list (optional, default = None)
      List of tuples (pos, col) specifying any colors in between start and
      end. In this context, 0. < pos < 1. specifiies the position of col
      (passed as RGB tuple) within the color map range.

    N : int (optional, default = 256)
      The number of rgb quantization levels.

    extend : string (optional, one of {*'neither'*, 'both', 'max', 'min'})
      Extend the colorbar and indicate this by triangles at the respective
      ends. See eg. here:

          http://matplotlib.org/examples/pylab_examples/contourf_demo.html

    over : 3-tuple (optional, default = None)
      Color definition for everything out of the upper range of the colormap.
      This is only meaningful if you set the ``extend`` option correctly.
      Uses ``end`` by default.

    under : 3-tuple (optional, default = None)
      Same as ``over`` but for the lower limit. Uses ``start`` by default.

    Returns
    -------
    cmap : LinearSegmentedColormap instance
        color map, ready to be used with matplotlib.

    Examples
    --------
    If you want a colormap ranging from tumblue over white to tumorange, you
    call this function via

    >>> cmap = create_cmap(start = tumcolors['tumblue'],
                           end   = tumcolors['tumorange'],
                           mid   = [(0.5, tumcolors['white'])]
                          )

    You can also go straight from tumblue to tumorange:

    >>> cmap = create_cmap(start = tumcolors['tumblue'],
                           end   = tumcolors['tumorange'])

    Or you can add several colors in between:

    >>> cmap = create_cmap(start = tumcolors['tumblue'],
                           end   = tumcolors['tumorange'],
                           mid   = [(0.3, tumcolors['white']),
                                    (0.7, tumcolors['black'])]
                           )

    """
    from matplotlib.colors import LinearSegmentedColormap

    cdict = dict()
    for i, channel in enumerate(['red', 'green', 'blue']):
        cdict_content = [[0.0, start[i], start[i]]]
        if mid is not None:
            try:
                for pos, col in mid:
                    cdict_content.append([pos, col[i], col[i]])
            except TypeError:
                pos, col = mid
                cdict_content.append([pos, col[i], col[i]])

        cdict_content.append([1.0, end[i], end[i]])
        cdict[channel] = cdict_content
    cmap = LinearSegmentedColormap('custom_cmap', cdict, N)

    # extend
    cmap.colorbar_extend = extend

    if under is None:
        under = start
    if over is None:
        over = end

    cmap.set_over(over)
    cmap.set_under(under)

    return cmap

# -------------
# PLOT GEOMETRY
# -------------

# constants for plot geometry
inch = 0.0254 # inch in mm, from scipy.constants
mm2inch = 1.0E-3 / inch
pt2inch = 1 / 72.27

# textwidth and -height using KOMA classes within latex on DIN-A4 paper
# see: KOMA Doku, 2012-07-22, p. 34

latex_geom = {# DIV        width   height (mm)
              'DIV=6'  :  (105.00, 148.50),
              'DIV=7'  :  (120.00, 169.71),
              'DIV=8'  :  (131.25, 185.63), # default 10pt fontsize
              'DIV=9'  :  (140.00, 198.00),
              'DIV=10' :  (147.00, 207.90), # default 11pt fontsize
              'DIV=11' :  (152.73, 216.00),
              'DIV=12' :  (157.50, 222.75), # default 12pt fontsize
              'DIV=13' :  (161.54, 228.46),
              'DIV=14' :  (165.00, 233.36),
              'DIV=15' :  (168.00, 237.60)}

# use the latex default also here
pagewidth, pageheight = latex_geom['DIV=10']


# this is the column width according to the aps styleguide
# --> PRL, PhysRev, JPC,...
apswidth = 86 * mm2inch

# actual plot geometry (in inch!)
golden_ratio = 1.618033988749895 # from scipy.constants
width =  pagewidth * mm2inch
height =  pagewidth/golden_ratio * mm2inch


# set some default values
def set_defaults(rcParams_inst, fontsize=None):
    """
    Set some plotting defaults. This is highly subjective, you may want to
    change/extend it. Note: This routine extends the default color name space
    of matplotlib by the tumcolors dictionary! This means you can directly
    access all tumcolors.

    Parameters
    ----------
    rcParams_inst : rcParams dictionary to be passed as obtained from
                    ``from matplotlib import rcParams``
    """
    if fontsize is None: fontsize = 11.0
    rcParams_inst['font.size'] = fontsize
    rcParams_inst['axes.linewidth'] = 0.5

    rcParams_inst['figure.figsize'] = (width, height)

    # nice stuff... update the matplotlib internal color dictionary
    __tumcolors_obj.extend_matplotlib_cache()

    ## legend
    # the number of points in the legend line
    #rcParams_inst['legend.numpoints'] = 1
    rcParams_inst['legend.fontsize'] = 'small'


    # this has changed for mpl > 2.0
    if matplotlib.__version__.startswith('2'):
        rcParams_inst['xtick.direction'] = 'in'
        rcParams_inst['ytick.direction'] = 'in'
        rcParams_inst['xtick.top'] = True
        rcParams_inst['ytick.right'] = True

    # the vertical space between the legend entries in fraction of fontsize
    # rcParams_inst['legend.labelspacing'] = 0.35
    # the length of the legend lines in fraction of fontsize
    # rcParams_inst['legend.handlelength'] = 1.5
    # the space between the legend line and legend text in fraction of fontsize
    # rcParams_inst['legend.handletextpad'] = 0.8

    # rendering simplicifactions (yield bad results, turn off by default)
    #rcParams_inst['path.simplify'] = True
    # The threshold of similarity below which vertices will be removed in the
    # simplification  process
    #rcParams_inst['path.simplify_threshold'] = 0.9

# activate latex font rendering
def set_latex(rcParams_inst, font=None, additional_packages=[]):
    r"""
    Set true LaTeX font rendering (not mathtext!). This offers you all the
    tools from LaTeX, including tables etc. In turn the explicit rendering
    requires quite some CPU time. Hence, it's best to only turn it on for the
    final version of a plot but not in between.

    Some packages are loaded by default (see source), font can be chosesn

    Parameters
    ----------
    rcParams_inst : rcParams dictionary to be passed as obtained from
                    ``from matplotlib import rcParams``

    font : String specifying the font used. Some of them listed below
           may not be available on your system:
           - helvetica (default and fallback)
           - myriadpro
           - minionpro
           - libertine
           - lmodern
           - times

    additional_packages : List of strings specifying further packages to be loaded.
                          Please, add one line per package, e.g.

                          >>> additional_packages = [r'\usepackage{amsmath}',
                          >>>                        r'\usepackage{amssymb}]'
    """
    rcParams_inst['text.usetex'] = True

    latex_preamble = []

    rcParams_inst['font.family'] = 'serif'
    packages = [
                r'\usepackage[group-decimal-digits = false]{siunitx}',
                r'\usepackage{amsmath}',
                r'\usepackage{braket}',
               ]

    siunitx_settings = [
                r'\DeclareSIUnit\atomicmassunits{amu}',
                r'\sisetup{mode = math}' #\sqrt of units
                ]

    if font is None:
        font='helvetica'

    font = font.lower()

    if font not in ['helvetica', 'myriadpro', 'minionpro', 'libertine',
        'lmodern', 'times', 'stix', 'cmbright']:
        raise ValueError('Font "{}" is not (yet) supported'.format(font))

    if font == 'helvetica':
        font_settings = [r'\renewcommand{\familydefault}{\sfdefault}',
                         r'\renewcommand*{\rmdefault}{\sfdefault}',
                         r'\usepackage{arevmath}',
                         r'\usepackage{helvet}',
                         r'\usepackage{sfmath}'
                         ]

    elif font == 'myriadpro':
        font_settings = [r'\usepackage[math, lf]{MyriadPro}',
                         r'\renewcommand{\familydefault}{\sfdefault}',
                         r'\renewcommand*{\rmdefault}{\sfdefault}',
                         ]

    elif font == 'minionpro':
        font_settings = [r'\usepackage[lf]{MinionPro}']

    elif font == 'libertine':
        font_settings = [r'\usepackage[lining]{libertineotf}',
                         r'\usepackage[libertine]{newtxmath}'
                         ]

    elif font == 'lmodern':
        font_settings = [r'\usepackage{lmodern}'
                         ]
    elif font == 'cmbright':
        font_settings = [r'\usepackage{cmbright}'
                         ]


    elif font == 'times':
        font_settings = [r'\usepackage{mathptmx}'
                       ]
    elif font == 'stix':
        font_settings = [r'\usepackage[notextcomp]{stix}']


    # crucial for some fonts
    latex_preamble.extend([r'\usepackage[T1]{fontenc}'])

    latex_preamble.extend(font_settings)
    latex_preamble.extend(packages)
    latex_preamble.extend(siunitx_settings)
    latex_preamble.extend(additional_packages)


    # new: tumcolor definitions
    colors = [r'\usepackage[names]{xcolor}']
    for line in __tumcolors_obj.export_latex(show=False).split('\n'):
        if line.startswith('%') or not line:
            continue
        else:
            colors.append(line)

    latex_preamble.extend(colors)
    rcParams_inst['text.latex.preamble'] = latex_preamble


def set_mathtext(rcParams_inst, family = 'serif'):
    """
    Enables mathtext rendering, for details see here:
    http://matplotlib.org/users/mathtext.html

    Parameters
    ----------
    family : String (*'serif'*, 'sans-serif')
             Font family chosen. Sans-serif corresponds to stixsans for math
             with Arial for normal text (did not find a better match),
             serif is stix with Times New
             Roman.
    """
    # make sure to turn off latex rendering
    rcParams_inst['text.usetex'] = False

    family = family.lower()
    if family == 'serif':
        # stix as default latex rendered font
        rcParams_inst['mathtext.fontset'] = 'stix'
        rcParams_inst['font.family'] = 'serif'
        rcParams_inst['font.serif'] = 'Times New Roman'
    elif family == 'sans-serif':
        rcParams_inst['mathtext.fontset'] = 'stixsans'
        rcParams_inst['font.family'] = 'Arial'

# wrapper function for PDF/EPS output
def write(filename, figure = None,
                    folder = None,
                    transparent = False,
                    write_info = False,
                    write_png = False,
                    write_pngviaeps = False,
                    write_pdf = True,
                    write_pdfviaeps = False,
                    write_eps = False,
                    write_svg = False,
                    purge_eps = False,
                    dpi = 300):
    """
    Wrapper funciton to write plots

    Parameters
    ----------
    filename : string
        Name of the output files (without filetype extension!)

    figure : plt.Figure instance (optional, default = None)
        Which figure to write (in case you have several of them...)

    folder : string
        Output folder, defaults to './output/'

    transparent : boolean (default = False)
        Transparency in the output file. May be problematic when embedding in
        pdfs.

    write_info : boolean (default = False)
        Write a text file with the plot dimensions (useful in combination with
        latex picture environment).

    write_png : boolean (default = False)
        Output in .png format (resolution --> dpi)

    write_pngviaeps : boolean (default = False)
        Output in .png format via eps output and convert

    write_pdf : boolean (default = True)
        Output in .pdf format

    write_pdfviaeps : boolean (default = False)
        Output in .pdf format via eps output and 'epstopdf'

    write_eps : boolean (default = False)
        Output in .eps format

    write_svg : boolean (default = False)
        Output in .svg format

    purge_eps : boolean (default = False)
        Remove intermediate *.eps files.

    dpi : integer (default = 300)
        resolution for pixel graphics
    """
    if folder is None:
        folder = 'output'
    if not os.path.isdir(folder):
        os.makedirs(folder)

    fileloc = os.path.join(folder, filename)

    if figure is None:
        savefig = plt.savefig
    else:
        savefig = figure.savefig

    if write_info:
        print('writing {}'.format(fileloc+'.info'))

        with file(fileloc+'.info', 'w') as out:
            out.write('Plot %s \ncreated: %s'%(filename, strftime('%c')))
            out.write('\n\nDimensions of plot (for latex export)')
            out.write(  '\n-------------------------------------')
            out.write('\nwidth  : %.2f inch = %.2f mm = %.2f pt'%(width, width/mm2inch,
             width/pt2inch))
            out.write('\nheight : %.2f inch = %.2f mm = %.2f pt'%(height,
             height/mm2inch, height/pt2inch))

    if write_eps or write_pdfviaeps or write_pngviaeps:
        print('writing {}'.format(fileloc+'.eps'))
        savefig(fileloc+'.eps', transparent = transparent)

        if write_pdfviaeps:
            print('Converting {0}.eps to {0}.pdf'.format(fileloc))
            subprocess.call('epstopdf {}.eps'.format(fileloc).split())
            # not to overwrite
            write_pdf=False

        if write_pngviaeps:
            print('Converting {0}.eps to {0}.png'.format(fileloc))
            subprocess.call('convert -density {1} {0}.eps {0}.png'.format(fileloc, dpi).split())
            # not to overwrite
            write_png=False

    if write_pngviaeps or write_pdfviaeps:
        if purge_eps:
            print('Removing intermediate file {}.eps'.format(fileloc))
            os.remove('{}.eps'.format(fileloc))

    if write_pdf:
        print('writing {}'.format(fileloc+'.pdf'))
        savefig(fileloc+'.pdf', transparent = transparent)

    if write_png:
        print('writing {}'.format(fileloc+'.png'))
        savefig(fileloc+'.png', dpi = dpi, transparent = transparent)

    if write_svg:
        print('writing {}'.format(fileloc+'.svg'))
        savefig(fileloc+'.svg', transparent = transparent)


def blend_colors(*args, **kwargs):
    """
    Blend two colors with a given ratio. Colors must defined by RGB tuples.

    Parameters
    ----------
    color1 : 3-tuple
        The first color, defined in RGB values.

    color2 : 3-tuple
        The second color, again in RGB values.

    ratio : float
        The blend ratio color1/color2.


    Returns
    -------
    color : 3-tuple
        The resulting color.
    """
    return __tumcolors_obj.blend_colors(*args, **kwargs)


def set_legend_handles_color(leg, color):
    """
    Function that changes the color of the legend handlers, a.k.a. the symbols
    and lines therein. This may be useful if you only want to indicate the
    linestyle, regardless of the color.

    Parameters
    ----------
    leg : legend instance
        The legend instance as returned by ax.legend() or fig.legend()

    color : matplotlib compatible color definition
        The color of the handles.

    Returns
    -------
    None
    """
    for l in leg.legendHandles:
        try:
            # this is for patches
            l.set_facecolor(color)
        except AttributeError:
            # this is for lines
            l.set_color(color)
    return None


def remove_legend_frame(leg):
    """
    Remove the frame around the legend (unfortunately there is no rcParams
    value to control this.)

    Parameters
    ----------
    leg : legend instance
        The legend instance as returned by ax.legend() or fig.legend()

    Returns
    -------
    None
    """
    leg.get_frame().set_linewidth(0)
    return None


def set_common_xlabel(label,
        fig=None,
        offset_x=0.00,
        offset_y=0.01,
        **kwargs
):
    """
    Writes common label for x axis onto figure centered horizontally.
    Any excess arguments are passed on to fig.text().

    Parameters
    ----------
    label : string
        Text to be written.

    fig : plt.Figure instance (default = None)
        Which figure to write on. If None, fig is obtained from plt.gcf().

    offset_x : float (default = 0.00)
        Value in figure coordinates by which the text is shifted to the right.

    offset_y : float (default = 0.01)
        Value in figure coordinates by which the text is shifted to the top.

    Returns
    -------
    None
    """
    if fig is None:
        fig = plt.gcf()
    x_center = .5*(fig.subplotpars.left + fig.subplotpars.right)
    halign = kwargs.pop("ha", "center")
    halign = kwargs.pop("horizontalalignment", halign)
    valign = kwargs.pop("va", "baseline")
    valign = kwargs.pop("verticalalignment", valign)
    fig.text(s=label,
        x=x_center+offset_x,
        y=offset_y,
        horizontalalignment=halign,
        verticalalignment=valign,
        **kwargs
    )
    return

def set_common_ylabel(label,
        fig=None,
        offset_x=0.01,
        offset_y=0.00,
        **kwargs
):
    """
    Writes common label for y axis onto figure centered vertically.
    Any excess arguments are passed on to fig.text().

    Parameters
    ----------
    label : string
        Text to be written.

    fig : plt.Figure instance (default = None)
        Which figure to write on. If None, fig is obtained from plt.gcf().

    offset_x : float (default = 0.01)
        Value in figure coordinates by which the text is shifted to the right.

    offset_y : float (default = 0.00)
        Value in figure coordinates by which the text is shifted to the top.

    Returns
    -------
    None
    """
    if fig is None:
        fig = plt.gcf()
    y_center = .5*(fig.subplotpars.bottom + fig.subplotpars.top)
    halign = kwargs.pop("ha", "left")
    halign = kwargs.pop("horizontalalignment", halign)
    valign = kwargs.pop("va", "center")
    valign = kwargs.pop("verticalalignment", valign)
    rotation = kwargs.pop("rotation", "vertical")
    fig.text(s=label,
        x=offset_x,
        y=y_center+offset_y,
        horizontalalignment=halign,
        verticalalignment=valign,
        rotation=rotation,
        **kwargs
    )
    return

def fill_between_range(x_vals, y_vals, ax, **kwargs):
    """
    Fill between a range of data series.

    Parameters
    ----------
    x_vals : 1D array
        The x-values corresponding to the y-data

    y_vals : List of 1D-arrays
        The data to be filled between. Must all be of same length!

    ax : The axis object to be plotted on.

    **kwargs: Are piped to pyplot's fill_between()

    Returns
    -------
    whatever fill_between() returns ;)
    """

    data = np.array(y_vals)

    max_data = np.max(data, axis=0)
    min_data = np.min(data, axis=0)

    return ax.fill_between(x=x_vals, y1=max_data, y2=min_data, **kwargs)


def set_axes_fontsize(ax, fontsize):
    """
    Set the font size of all text on an axes object : ticks, labels,
    ticklabels, title; but not (!) the legend.

    Parameters
    ----------
    ax : mpl axes object
        The axes object for which the fontsize is to be changed.

    fontsize : integer/string
        Pyplot compatible fontsize specifier.

    Returns
    -------
    ax : mpl axes object
        The input ax object
    """

    for item in ([ax.title,
                  ax.xaxis.label,
                  ax.yaxis.label]
                 + ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(fontsize)

    return ax
