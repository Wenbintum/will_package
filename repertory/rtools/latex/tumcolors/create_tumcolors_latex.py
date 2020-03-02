#!/usr/bin/env python

# This little script creates a document with all tumcolors in it

import os
import subprocess
import time
import rtools.tumcd

tumcolors = rtools.tumcd.TUMcolors()

doc = r"""
\documentclass{scrartcl}
\usepackage[names]{xcolor}
\usepackage{array}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{url}
"""[1::]

# color definitions
doc += tumcolors.export_latex(show = False)

doc += "\n\n"+r"\begin{document}"

doc +=r"""
\section*{TUM Corporate Design Color Definitions}
The color definitions listed below are available via the \texttt{rtools.tumcd.export\_latex()} function. They are defined as mentioned in the TUM CD guide available at \url{https://portal.mytum.de/corporatedesign/print/styleguide/styleguide_print_band2.pdf/}. Colors for diagrams are as well available as blends with white in defined ratios. Just append \texttt{\_X} to the color name, where \texttt{X} is the mixing ratio as mentioned in the table.

"""


maincolors = tumcolors.maincolors
accentcolors = tumcolors.accentcolors
diagcolors = tumcolors.diagcolors
ratios = tumcolors.ratios


# the main colors table
doc += r"""
\begin{longtable}{l m{7cm}}
\toprule
\multicolumn{2}{c}{\textbf{Main colors (``Hausfarben'')}}"""

for c in sorted(maincolors.keys()):
    doc += "\n" + r"\\\midrule" + "\n"
    doc += r"\texttt{{{0:s}}} & \cellcolor{{{1:s}}}".format(c.replace('_','\_'),c) 

doc += r"""
\\\bottomrule
\end{longtable}

"""

# the accent colors table
doc += r"""
\begin{longtable}{l m{7cm}}
\toprule
\multicolumn{2}{c}{\textbf{Extended accent colors (for presentations only!)}}"""

for c in sorted(accentcolors.keys()):
    doc += "\n" + r"\\\midrule" + "\n"
    doc += r"\texttt{{{0:s}}} & \cellcolor{{{1:s}}}".format(c.replace('_','\_'),c) 

doc += r"""
\\\bottomrule
\end{longtable}

"""

# the diagram colors table
doc += r"""
\begin{longtable}{l m{2cm} m{2cm} m{2cm} m{2cm}}
\toprule
\multicolumn{5}{c}{\textbf{Extended diagram colors and respective blends with white}}
\\\midrule
& 
"""
for r in ratios:
    doc += r"&\texttt{{$\ast$\_{}}}".format(r)

for c in sorted(diagcolors.keys()):
    doc += "\n" + r"\\\midrule" + "\n"
    doc += r"\texttt{{{0:s}}} & \cellcolor{{{1:s}}}".format(c.replace('_','\_'),c) 
    for r in ratios:
        doc += r" & \cellcolor{{{0:s}_{1:s}}}".format(c,r)

doc += r"""
\\\bottomrule
\end{longtable}

"""


doc += r"""\vfill\hfill\itshape This document was generated on {}""".format(time.strftime("%c"))

doc += r"""
\end{document}
"""


#------------------------------------------------------------------------------
# Create the latex document
#------------------------------------------------------------------------------
fname = "tumcolors.tex"
folder = "tumcolors"
if not os.path.exists(folder):
    os.makedirs(folder)

with open(os.path.join(folder,fname), 'w') as f:
    f.write(doc)

os.chdir(folder)

subprocess.call("latexmk -pdf {}".format(fname).split())
subprocess.call("latexmk -c".split())

