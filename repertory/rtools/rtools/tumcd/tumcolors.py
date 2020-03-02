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

from __future__ import print_function

import copy
import time

from matplotlib.colors import rgb2hex

class TUMcolors(object):
    """
    Class handling the colors defined in the TUM styleguide.
    All colors are internally defined in RGB code (CMYK support to be added),
    ranging from 0-255

    ---
    Simon P. Rittmeyer, 2014
    simon.rittmeyer(at)tum.de
    """

    def __init__(self):
        # ----------
        # TUM COLORS
        # ----------
        # 'official colors' defined in the TUM corporate design styleguide as
        # of October 8th 2014:
        # https://portal.mytum.de/corporatedesign/print/styleguide/styleguide_print_band2.pdf/

        # recommended main colors from the styleguide
        self.maincolors = {
                     # These are the three 'Hausfarben'
                     'tumblue' : [0, 101, 189],# Pantone 300
                     'black'   : [0, 0, 0],
                     'white'   : [255, 255, 255],
                     # 'Zusatzfarben - Blau'
                     'pantone540' : [0, 51, 89],
                     'pantone301' : [0, 82, 147],
                     'pantone300' : [0, 101, 189],
                     'pantone542' : [100, 160, 200],
                     'pantone283' : [152, 198, 234],
                     # just an alias for pantone 301 and pantone 283
                     'tumdarkblue' : [0, 82, 147],
                     'tumlightblue' : [152, 198, 234],
                     # alias for convenience - is just diag_red
                     'tumred' : [196, 7, 27],
                     # 'Zusatzfarben - Grau'
                     'darkgray'   : [88, 88, 90],
                     'mediumgray' : [156, 157, 159],
                     'lightgray'  : [217, 218, 219],
                     # 'Akzentfarben'
                     'tumgreen'  : [162, 173, 0], # Pantone 383
                     'tumorange' : [227, 114, 34], # Pantone 158
                     'tumivory'  : [218, 215, 203] #Pantone 7527
                     }

        # 'erweiterte Farbpalette fuer Diagramme und Inforgrafiken'
        # intended for multi-color diagramms if you run out of
        # 'Hausfarben' and 'Akzentfarben'
        self.diagcolors = {
                     'diag_purple'     : [105, 8, 90],
                     'diag_violet'     : [15, 27, 95],
                     'diag_pantone540' : [0, 51, 89],
                     'diag_pantone301' : [0, 82, 147],
                     'diag_pantone300' : [0, 101, 189],
                     'diag_pantone542' : [100, 160, 200],
                     'diag_pantone283' : [152, 198, 234],
                     'diag_petrol'     : [0, 119, 138],
                     'diag_darkgreen'  : [0, 124, 48],
                     'diag_green'      : [103, 154, 29],
                     'diag_tumgreen'   : [162, 173, 0],
                     'diag_tumivory'   : [218, 215, 203],
                     'diag_yellow'     : [255, 220, 0],
                     'diag_gold'       : [249, 186, 0],
                     'diag_orange'     : [214, 76, 13],
                     'diag_tumorange'  : [227, 114, 34],
                     'diag_red'        : [196, 7, 27],
                     'diag_darkred'    : [156, 13, 22]
                     }

        # further 'Akzentfarben' for presentations only
        self.accentcolors = {
                     'acc_yellow'     : [255, 180, 0],
                     'acc_orange'     : [255, 128, 0],
                     'acc_red'        : [229, 52, 24],
                     'acc_darkred'    : [202, 33, 63],
                     'acc_blue'       : [0, 153, 255],
                     'acc_lightblue'  : [65,  190, 255],
                     'acc_green'      : [145, 172, 107],
                     'acc_lightgreen' : [181, 202, 130]
                     }

        # blend the diagram colors with white as mentioned in the style guide
        # ratios are defined in the style guide
        self.ratios = ['85', '70', '55']
        self.diagcolors_blended = self.__create_blended_palette(palette = self.diagcolors,
                                                                ratios = self.ratios)


        # Unify everything in one palette
        self.tumcolors = dict()
        for i in [self.maincolors, self.diagcolors_blended, self.accentcolors]:
            self.tumcolors.update(i)

        # internal hex dictionary for web applications
        self.maincolors_hex = {k : rgb2hex(v) for k,v in self.__convert_to_plt_palette(self.maincolors).items()}
        self.diagcolors_blended_hex = {k : rgb2hex(v) for k,v in self.__convert_to_plt_palette(self.diagcolors_blended).items()}
        self.accentcolors_hex = {k : rgb2hex(v) for k,v in self.__convert_to_plt_palette(self.accentcolors).items()}
        self.tumcolors_hex = {k : rgb2hex(v) for k,v in self.__convert_to_plt_palette(self.tumcolors).items()}

    def blend_colors(self, color1, color2, ratio):
        """
        Blend two colors with a given ratio. Colors must defined by RGB tuples.
        """
        assert len(color1) == len(color2), "Can't blend given colors"

        return [ratio*color1[i] + (1.-ratio)*color2[i] for i in range(len(color1))]


    def __create_blended_palette(self, palette, ratios):
        """
        Create a palette by blending all contained colors with white by given
        ratio.
        """
        # blend the colors with white
        # ratios are defined in the style guide
        if not isinstance(ratios, list): ratios = list(ratios)
        blended_palette = dict()
        for name, color in palette.items():
            for ratio in ratios:
                x = float(ratio) / 100.
                blended_color = self.blend_colors(color, self.maincolors['white'], x)
                blended_palette['{0}_{1}'.format(name, ratio)] = blended_color

        # add original unblended colors
        blended_palette.update(palette)

        return blended_palette


    def __convert_to_plt_palette(self, orig_palette):
        """
        Convert a palette from RGB ranges [0; 255] to [0,1] as required my
        matplotlib.
        """
        plt_palette = copy.deepcopy(orig_palette)
        # matplotlib requires an RGB range [0,1]
        for name, color in plt_palette.items():
                plt_palette[name] = [i/255. for i in color]
        return plt_palette


    def export_matplotlib(self):
        """
        Export the TUMColors for matplotlib.

        Returns
        -------
        matplotlib palette
        """

        return self.__convert_to_plt_palette(self.tumcolors)

    def extend_matplotlib_cache(self):
        """
        Extends matplotlibs color cache with the TUMcolors :).

        Returns
        -------
        None
        """

        # nice stuff... update the matplotlib internatl internal color
        # dictionary
        from matplotlib.colors import ColorConverter
        colors = self.export_matplotlib()

        # Those two cause trouble if updated
        colors.pop('black', None)
        colors.pop('white', None)

        ColorConverter.cache.update(colors)


    def export_gimp(self, save_file=False):
        """
        Export the TUMColors for GIMP as GIMP color palette (.gpl)

        To install, copy the palette to ``~/.gimp-2.8/palettes``

        Parameters
        ----------
        save_file : boolean, optional
            If True, write the palette to a file (tumcolors.gpl).

        Returns
        -------
        s : string
            The GIMP palette as string.
        """

        s = r"""GIMP Palette
Name: TUMColors
Columns: 3
# generated by rtools module on
# {}""".format(time.strftime('%c'))

        s += """
#
# These are the main colors ('Hausfarben') that are intended to be used in printed work
#"""
        for name in sorted(self.maincolors.keys()):
            s+= "\n" + "{1:d} {2:d} {3:d} {0:s}".format(name, *self.maincolors[name])

        s += r"""
#
# This is the extended color palette for presentations only!
#"""
        s += 5*"\n0 0 0  PRESENTATIONS -->"
        for name in sorted(self.accentcolors.keys()):
            s+= "\n" + "{1:d} {2:d} {3:d} {0:s}".format(name, *self.accentcolors[name])

        s += r"""
#
# This is the extended color palette for diagramms including blends with white
#"""
        s += 5*"\n0 0 0 DIAGRAMMS -->"
        for name in sorted(list(self.diagcolors.keys()) + self.diagcolors_blended.keys()):
            s+= "\n" + "{1:3d} {2:3d} {3:3d} {0:s}".format(name, *map(lambda x: int(round(x)), self.tumcolors[name]))


        #print s
        if save_file:
            with open("tumcolors.gpl", "w") as f:
                f.write(s)
        else:
            return s


    def export_inkscape(self, save_file=False):
        """
        Export the TUMColors for Inkscape as GIMP color palette (.gpl)

        To install, copy the palette to ``~/.config/inkscape/palettes``
        On MacOSX, the respective path is

            ``/Applications/Inkscape.app/Contents/Resources/share/inkscape/palettes``

        i.e. directly in the app folder. You may change to
        ``~/Applications/...`` if inkscape was not installed globally

        Parameters
        ----------
        save_file : boolean, optional
            If True, write the palette to a file (tumcolors.gpl).

        Returns
        -------
        s : string
            The GIMP palette as string.
        """

        return self.export_gimp(save_file)


    def export_latex(self, show = True, save_file=False):
        r"""
        Export the TUMColors for LaTeX.

        To use, add the color definitions to your LaTeX document.
        Please note that the package 'xcolor' has to be loaded in order to
        get the color definitions to work!

        >>> \usepackage[names]{xcolor}
        
        Parameters
        ----------
        save_file : boolean, optional
            If True, write the palette to a file (tumcolors.tex).

        Returns
        -------
        s : string
            The palette as string.
        """
        # note that curly braces have to be escaped... use double braces!
        s = r"""
% -----------------------------------------------------------------------------
% This is the color palette as recommended in the TUM styleguide:
% https://portal.mytum.de/corporatedesign/print/styleguide/styleguide_print_band2.pdf/
%
% Please note that the package 'xcolor' has to be loaded in order to get the
% following color definitions to work
%
% \usepackage[names]{{xcolor}}
%
% exported using the rtools module on
% {}
% -----------------------------------------------------------------------------
""".format(time.strftime('%c'))[1::]

        s += """
% These are the main colors ('Hausfarben') that are intended to be used in
% printed work"""

        for name in sorted(self.maincolors.keys()):
            s+= "\n" + r"\definecolor{{{0:s}}}{{RGB}}{{{1:3d}, {2:3d}, {3:3d}}}".format(name, *self.maincolors[name])

        s += "\n" + r"""
% This is the extended color palette for presentations only!"""

        for name in sorted(self.accentcolors.keys()):
            s+= "\n" + r"\definecolor{{{0:s}}}{{RGB}}{{{1:3d}, {2:3d}, {3:3d}}}".format(name, *self.accentcolors[name])

        s += "\n" + r"""
% This is the extended color palette for diagramms"""
        for name in sorted(self.diagcolors.keys()):
            s+= "\n" + r"\definecolor{{{0:s}}}{{RGB}}{{{1:3d}, {2:3d}, {3:3d}}}".format(name, *self.diagcolors[name])

        s += "\n" + r"""
% All colors may be blended with white in given ratios. These are denoted
% with subscripts indicating the blending ratio (85%, 75%, and 55%).
%
% Here, we make use of the xcolor package to create the blended colors
%"""
        for name in sorted(self.diagcolors.keys()):
            for ratio in self.ratios:
                s+= "\n" + r"\colorlet{{{0:s}_{1:s}}}{{{0:s}!{1:s}!white}}".format(name, ratio)

        if show:
            print(s)

        if save_file:
            with open("tumcolors.tex", "w") as f:
                f.write(s)
        else:
            return s


    def show_colors(self):
        import matplotlib.pyplot as plt

        # create the figure
        fig = plt.figure()

        # Ok, this is quick'n'dirty
        palettes = [self.maincolors,
                    self.accentcolors,
                    self.diagcolors]

        # get the matplotlib palette
        tumcolors = self.export_matplotlib()

        titles = ['"Hausfarben"',
                  'Additional colors (for presentations only!)',
                  'Extended color palette for diagrams (including blended colors)']

        # increment for ploting blended colors
        inc = 0.25

        # plto linewidth
        lw = 5
        for i, palette in enumerate(palettes):
            ax = fig.add_subplot(3, 1, i+1)

            # sort colors by names
            names = sorted(palette.keys())
            for j, name in enumerate(names):
                if i != 2:
                    # main and accent colors: no blended colors
                    ax.axhline(y = j, color = tumcolors[name], lw = lw)
                    ax.set_xticks([])
                else:
                    # show different blend steps for diag colors
                    ax.plot([0, inc], [j, j], color = tumcolors[name], lw = lw)
                    for k, ratio in enumerate(self.ratios):
                        ax.plot([(k+1)*inc, (k+2)*inc], [j, j],
                                color = tumcolors['{0}_{1}'.format(name, ratio)],
                                lw = lw)
                    ax.set_xticks([inc * (l+1) + inc / 2. for l in range(len(self.ratios))])
                    ax.set_xticklabels(['_{}'.format(l) for l in self.ratios])

            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names)
            ax.set_ylim(-1, len(names))
            ax.set_title(titles[i])

        for k in range(len(self.ratios)):
            ax.axvline(x = inc * (k+1), color = 'black', lw = 1, ls = '--')

        plt.show()


