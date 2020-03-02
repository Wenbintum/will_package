from matplotlib import rcParams
import numpy as np
import matplotlib.pyplot as plt
import rtools.helpers.matplotlibhelpers as matplotlibhelpers
from rtools.helpers.matplotlibhelpers import tumcolors,create_cmap, show_colors
from scipy.constants import golden_ratio
import os,sys

class plot_of_energies():
    
    """ simple class to plot a figure """
    def __init__(self):
        self.path = os.getcwd()
        self.colors = [tumcolors['tumorange'],tumcolors['diag_pantone300_85'],tumcolors['diag_red_85'],
                       tumcolors['diag_purple_70'],tumcolors['diag_red_85'],tumcolors['pantone300'],
                       tumcolors['tumred'],tumcolors['tumlightblue'],tumcolors['acc_red'],tumcolors['tumorange'],
                       tumcolors['lightgray'],tumcolors['acc_lightblue'],tumcolors['pantone283'],
                       tumcolors['tumgreen'],tumcolors['tumorange'],tumcolors['tumivory'],tumcolors['pantone542'],
                       tumcolors['darkgray'],tumcolors['pantone301'],tumcolors['acc_yellow']]


    def _set_plotting_env(self,width=None,height=None,lrbt=None):
        if (width == None and height == None):
            width = 3.37
            height = width / golden_ratio *1.5/2 +1
        if (lrbt == None):
            lrbt = [0.135,0.955,0.25,0.78]
        # set plot geometry
        rcParams['figure.figsize'] = (width, height) # x,y
        #rcParams['font.weight'] = 'medium' #'bold'
        #rcParams['font.style'] = 'normal' #'italic'
        rcParams['font.size'] = 12.0
        #rcParams['mathtext.fontset'] = 'cm'#'stix', 'cm'
        rcParams['figure.subplot.left'] = lrbt[0]   # the left side of the subplots of the figure
        rcParams['figure.subplot.right'] = lrbt[1]  # the right side of the subplots of the figure
        rcParams['figure.subplot.bottom'] = lrbt[2] # the bottom of the subplots of the figure
        rcParams['figure.subplot.top'] = lrbt[3]    # the top of the subplots of the figure
        rcParams['figure.subplot.wspace'] = 0.2
        rcParams['figure.subplot.hspace'] = 0.2
        #the good latex math fonts:
        rcParams['text.usetex'] = True
        latex_preamble = []
        rcParams['font.family'] = 'serif'
        packages = [ r'\usepackage[group-decimal-digits = false]{siunitx}',
                     r'\usepackage{amsmath}',
                     r'\usepackage{braket}',  ]
        siunitx_settings = [r'\DeclareSIUnit\atomicmassunits{amu}',
                            r'\sisetup{mode = math}'] #\sqrt of units
        font_settings = [r'\usepackage{lmodern}']
        latex_preamble.extend([r'\usepackage[T1]{fontenc}'])
        latex_preamble.extend(font_settings)
        latex_preamble.extend(packages)
        latex_preamble.extend(siunitx_settings)
        colors = [r'\usepackage[names]{xcolor}']
        latex_preamble.extend(colors)
        rcParams['text.latex.preamble'] = latex_preamble

plt_template=plot_of_energies()
plt_template._set_plotting_env(width=None,height=None,lrbt=[0.2,0.95,0.25,0.85])
fig1 = plt.figure()
ax = fig1.add_subplot(111)
x=np.random.rand(100)
y=np.sin(x)
ax.plot(x,y)
plt.show()