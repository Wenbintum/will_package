#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os
import matplotlib.ticker as ticker
from scipy.constants import golden_ratio
from scipy import constants
import rtools.helpers.matplotlibhelpers as matplotlibhelpers

from rtools.helpers.matplotlibhelpers import tumcolors,create_cmap, show_colors




HtoeV=constants.physical_constants["Hartree energy in eV"][0]



def S(x): #overlap integral
    return (1+x+(1./3)*x**2)*np.exp(-x)

def J(x):
    #coulomb integral
    return 1./x - np.exp(-2*x)*(1+1./x)

def K(x):
    #exchange integral
    return (1+x)*np.exp(-x)

def enB(x,E1s):   #bonding orbital energy at x
    return E1s + 1./x - (J(x)+K(x))/(1+S(x)) 

def enAB(x,E1s): #antibonding orbital energy at x
    return E1s + 1./x + (-J(x)+K(x))/(1-S(x))



class plot_of_energies():

    """ simple class to plot a figure """
    def __init__(self):
        self.path = os.getcwd()
        self.colors = [tumcolors['tumorange'],tumcolors['diag_pantone300_85'],tumcolors['diag_red_85'],tumcolors['diag_purple_70'],tumcolors['diag_red_85'],tumcolors['pantone300'],tumcolors['tumred'],tumcolors['tumlightblue'],tumcolors['acc_red'],tumcolors['tumorange'],tumcolors['lightgray'],\
                       tumcolors['acc_lightblue'],tumcolors['pantone283'],tumcolors['tumgreen'],tumcolors['tumorange'],\
                                              tumcolors['tumivory'],tumcolors['pantone542'],tumcolors['darkgray'],tumcolors['pantone301'],\
                                                                     tumcolors['acc_yellow']]





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


    def execute(self):
        self._set_plotting_env(width=None,height=None,lrbt=[0.2,0.95,0.25,0.85]) #for eps
        
        fig1 = plt.figure()
        ax = fig1.add_subplot(111)
        
        ymin=-0.2;ymax=1;
        xmin=0.000001;xmax=5;
        ax.set_ylim(ymin,ymax)
        ax.set_xlim(xmin,xmax)
        ax.tick_params(
                axis='x',         # changes apply to the x-axis
                which='both',     # both major and minor ticks are affected
                bottom='on',      # ticks along the bottom edge are off
                top='on',         # ticks along the top edge are off
                labelbottom='on') # labels along the bottom edge are off
        
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1)); 
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5)); 
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2));
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1));
  
        E1s=-13.6/HtoeV   #Hartree, approx
        x = np.linspace(xmin,xmax,1000)
        energyB = enB(x,E1s)
        energyAB = enAB(x,E1s)
        #ax.annotate(r'$\epsilon_{+}$', xy=(0.8,0.2))#,size=2,color="k")
        #ax.annotate(r'$\epsilon_{-}$', xy=(0.3,1.3))#,size=12,color="k")

        ax.plot(x,energyB-E1s,color=[0.0, 0.396078431372549, 0ls.7411764705882353],lw=2,label=r'$\epsilon_{+}$(B)')
        #ax.plot(x,energyAB-E1s,color=[0.7686274509803922, 0.027450980392156862, 0.10588235294117647],lw=2,label=r'$\epsilon_{-}$(AB)') 
        ax.plot(x,energyAB-E1s,color=tumcolors['tumorange'],lw=2,label=r'$\epsilon_{-}$(AB)') 
        ax.axhline(0,lw=0.5,color='k',ls='--')

        emin=np.amin(energyB-E1s)
        xmin=x[np.where(energyB-E1s==emin)]
        

        ax.annotate(r'R$_{min}$='+'{}'.format(round(xmin,2))+r'a$_0$,'+r' E$_{min}$'+'={}'.format(round(emin,2))+'Ha', xy=(2,0.4),size=6,color='k')#,size=12,color="k")
        ax.annotate(r'', xy=(xmin,emin),xytext=(xmin,0.4),size=4,arrowprops=dict(arrowstyle="->",connectionstyle="arc3",color="k"))
        
        ax.set_xlabel(r'R [a$_{0}$]')#,size=12)
        ax.set_ylabel(r'$\epsilon$-E$_{1s}$ [Hartree]')#,size=12)
        plt.legend(fontsize=8) 
        fig1.suptitle(r'LCAO Binding Energy of H$_{2}^{+}$')#,fontsize=8)
        
        #plt.savefig('energies.png',dpi=300,transparent=False)
        figname='template'
        matplotlibhelpers.write(figname,transparent=True,write_info = False,write_png=True,write_pdf=True,write_eps=True)



if __name__ == "__main__":

    a=plot_of_energies()
    a.execute()






