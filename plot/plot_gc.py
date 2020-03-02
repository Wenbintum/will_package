#!/usr/bin/env python

import numpy as np
import numpy.matlib
import scipy.linalg as SP
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
from scipy import constants
import sys
import matplotlib.pyplot as plt
from rtools.helpers.matplotlibhelpers import tumcolors,create_cmap, show_colors
import rtools.helpers.matplotlibhelpers as matplotlibhelpers
#from scipy.constants import golden_ratio, inch
from matplotlib import rcParams
import matplotlib.ticker as ticker
import os
#import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import subprocess
from scipy.constants import golden_ratio, inch
from gamma_test2 import gamma_test2
#from get_couplings import get_couplings


HtoeV=constants.physical_constants["Hartree energy in eV"][0]
autime=constants.physical_constants["atomic unit of time"][0]*1E15 #in fs\        ??????




class xy_plot():

    """ simple class to plot a figure """
    def __init__(self):
        self.path = os.getcwd()
        self.colors = [tumcolors['tumorange'],tumcolors['diag_pantone300_85'],tumcolors['diag_red_85'],tumcolors['diag_purple_70'],tumcolors['diag_red_85'],tumcolors['pantone300'],tumcolors['tumred'],tumcolors['tumlightblue'],tumcolors['acc_red'],tumcolors['tumorange'],tumcolors['lightgray'],\
                       tumcolors['acc_lightblue'],tumcolors['pantone283'],tumcolors['tumgreen'],tumcolors['tumorange'],\
                       tumcolors['tumivory'],tumcolors['pantone542'],tumcolors['darkgray'],tumcolors['pantone301'],\
                       tumcolors['acc_yellow']]


    def _set_plotting_env(self,width=None,height=None,lrbt=None):
        if (width == None and height == None):
            #width = 3.25 #ACS
            width = 3.37 +0.2
            height = width / golden_ratio *1.5/2  + 0.2
        if (lrbt == None):
            lrbt = [0.135,0.955,0.25,0.78]
        #print width,height
        # set plot geometry
        rcParams['figure.figsize'] = (width, height) # x,y
        #rcParams['font.family'] = 'serif' #'serif', 'sans-serif', 'monospace'
        #rcParams['font.serif'] = 'Computer Modern Roman'#'Times New Roman'  
        #to see options:  import matplotlib.font_manager         for font in matplotlib.font_manager.fontManager.ttflist: print(font.name)       
        #rcParams['font.weight'] = 'medium' #'bold'
        #rcParams['font.style'] = 'normal' #'italic'
        rcParams['font.size'] = 8.0
        #rcParams['mathtext.fontset'] = 'cm'#'stix', 'cm'
        rcParams['figure.subplot.left'] = lrbt[0]  # the left side of the subplots of the figure
        rcParams['figure.subplot.right'] = lrbt[1] #0.965 # the right side of the subplots of the figure
        rcParams['figure.subplot.bottom'] = lrbt[2] # the bottom of the subplots of the figure
        rcParams['figure.subplot.top'] = lrbt[3] # the bottom of the subplots of the figure
        rcParams['figure.subplot.wspace'] = 0.2
        rcParams['figure.subplot.hspace'] = 0.2

        rcParams['axes.linewidth'] = 0.5 #rcParams['axes.linewidth'] *scale
        matplotlibhelpers.set_latex(rcParams,font = "lmodern") #paper         #these override the rcParams fonts above...
       # matplotlibhelpers.set_latex(rcParams,font = "helvetica") #poster





    def plot_gc_inner(self,mu,sysindex,Ecenter_up,Ecenter_dn, mtag,donor_index_local,use_resonance,resonance):
        self._set_plotting_env(width=None,height=None,lrbt=[0.15,0.87,0.2,0.92]) #for eps
    #    dosup = np.loadtxt('dos_lorentzian_up{}.txt'.format(mtag))   #these are shifted to Efermi and are in eV.
    #    dosdn = np.loadtxt('dos_lorentzian_dn{}.txt'.format(mtag))   #these are independent of the chosen donor state.
        
        #gammaup = np.loadtxt('gamma_test_up_m2.txt')
        #gammadn = np.loadtxt('gamma_test_dn_m2.txt')
        gammaup = np.loadtxt('method{}/gamma_test_donor={}_{}{}RAW.txt'.format(mtag,donor_index_local,'up',mtag))   #depends on the donor.  RAW unshifted eV energies.
        gammadn = np.loadtxt('method{}/gamma_test_donor={}_{}{}RAW.txt'.format(mtag,donor_index_local,'dn',mtag))
        
        habup = np.loadtxt('method{}/habup_donorindex{}{}RAW.txt'.format(mtag,donor_index_local,mtag))    #RAW eV
        habdn = np.loadtxt('method{}/habdn_donorindex{}{}RAW.txt'.format(mtag,donor_index_local,mtag))       



        #xmax=5
        #xmin=-5
        for plotgamma in [True,False]:
            for size in ['SMALL','LARGE']:
                if size == 'SMALL': xmax=6;xmin=-6
                elif size == 'LARGE': xmax=10;xmin=-10
        #        updos_inrange = [ dosup[i,1] for i in range(len(dosup[:,0])) if (dosup[i,0] <= xmax) and (dosup[i,0] >= xmin) ]
        #        dndos_inrange = [ dosdn[i,1] for i in range(len(dosdn[:,0])) if (dosdn[i,0] <= xmax) and (dosdn[i,0] >= xmin) ]
        #        ymaxup=np.max(updos_inrange)#np.array(DOS[0][1])[:,1])
        #        ymaxdn=np.max(dndos_inrange)#np.array(DOS[1][1])[:,1])
        #        ymax = np.max((ymaxup,ymaxdn))*1.2
                #find range for couplings**1
 
                for exponent in [1]:  #2]:
                    cup_inrange = [ abs(habup[i,exponent+2])*1000. for i in range(len(habup[:,0])) if (habup[i,1] <= xmax+mu) and (habup[i,1] >= xmin+mu) ]
                    cdn_inrange = [ abs(habdn[i,exponent+2])*1000. for i in range(len(habdn[:,0])) if (habdn[i,1] <= xmax+mu) and (habdn[i,1] >= xmin+mu) ]
                    #print('{}'.format(len(cup_inrange)))
                    #print('{}'.format(len(cdn_inrange)))
                    #print('{}'.format(np.max(cup_inrange)))
                    #print('{}'.format(np.max(cdn_inrange)))
                    ycmaxup=np.max(cup_inrange)#np.array(DOS[0][1])[:,1])
                    ycmaxdn=np.max(cdn_inrange)#np.array(DOS[1][1])[:,1])
                    ycmax = np.max((ycmaxup,ycmaxdn))*1.3
                    #TEST TEST
                    #ycmax = 1000  #TEST TEST
                    ycmin=0.0   #unless log
 
                    sigma=2  #the second value of sigma used is 0.25 eV
                    gup_inrange = [ gammaup[i,sigma] for i in range(len(gammaup[:,0])) if (gammaup[i,0] <= xmax+mu) and (gammaup[i,0] >= xmin+mu) ]
                    gdn_inrange = [ gammadn[i,sigma] for i in range(len(gammadn[:,0])) if (gammadn[i,0] <= xmax+mu) and (gammadn[i,0] >= xmin+mu) ]
                    #print('{}'.format(gup_inrange))
                    #print('{}'.format(gdn_inrange))
                    #print('{}'.format(len(gup_inrange)))
                    #print('{}'.format(len(gdn_inrange)))
                    #print('{}'.format(np.max(gup_inrange)))
                    #print('{}'.format(np.max(gdn_inrange)))
                    if gup_inrange != [] and gdn_inrange != []:
                        ygmaxup=np.max(gup_inrange)#np.array(DOS[0][1])[:,1])
                        ygmaxdn=np.max(gdn_inrange)#np.array(DOS[1][1])[:,1])
                        ygmax = np.max((ygmaxup,ygmaxdn))*1.1
                    else: ygmax=1
                    ygmin=0.0
 
 
 
 
 
                    for uselog in [False,True]:
                        fig1 = plt.figure()
                       
                        ax = fig1.add_subplot(211)
                        
                     #   print('dos ymax for the domain is {}'.format(ymax))
                  #      ax.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                  #      ax.set_ylim(0,ymax)  #-1*HtoeV,1.5*HtoeV)
                                     
                        #ycmax = np.max((ycmaxup,ycmaxdn))*1.5
                        #if exponent==1: ycmin=10e-8                   #; ycmax = np.max((ycmaxup,ycmaxdn))*1.5
                        #elif exponent==2:  ycmin=(10e-8*HtoeV)**2     #;ycmax=0.1*HtoeV**2;
                        #ycmin=0.
                        #ycmax=0.1*HtoeV**2
                        #ycmax = np.max((ycmaxup,ycmaxdn))*1.6
                        if uselog: 
                            ycmax = ycmax*100 #np.max((ycmaxup,ycmaxdn))*1000; 
                            if exponent==1: ycmin=10e-4
                            elif exponent==2: ycmin=(10e-4*HtoeV)**2    
                        
                        #print('max coupling**2 in range is up {} dn {} '.format(ycmaxup, ycmaxdn))
                        print('ycmin, ycmax is {} {} '.format(ycmin,ycmax)) 
                    
                 #       ax.plot( dosup[:,0], dosup[:,1],linewidth=1.0,label='up',color=tumcolors['mediumgray'],zorder=0)
                        
                        #ax.annotate(r'$\text{Ar4s}$', xy=(0.68,0.7),textcoords='axes fraction',size=9,color="k")
                   #     ax.annotate('d{}'.format(donor_index_local), xy=(Ecenter_up,0.7),textcoords=('data','axes fraction'),size=9,color="k")
##                       ax.annotate(r'', xy=(0.95,0.85),xycoords='axes fraction',xytext=(0.95,0.45),textcoords='axes fraction',size=9,color="w",arrowprops=dict(arrowstyle="->",connectionstyle="arc3",color="k"),zorder=1)
                        ax.axvline(x=Ecenter_up, ymin=0., ymax=10.,linewidth=1,linestyle='-',color=tumcolors['tumred'],zorder=0)          
                        if use_resonance:
                            ax.axvline(x=resonance, ymin=0., ymax=100.,linewidth=1,linestyle='--',color=tumcolors['tumred'],zorder=0)          
                            ax.annotate('Ar4s', xy=(resonance,0.7),textcoords=('data','axes fraction'),size=9,color="k")
                        ax.axvline(x=0, ymin=0., ymax=1000.,linewidth=0.5,linestyle='--',color=tumcolors['black'],zorder=0)
                        
                	if True: #coupling stuff
                            #ax1 = ax.twinx()
                            width=0.05
                            #couplings Had in meV units.
                            if uselog: ax.bar( habup[:,1]-mu,abs(habup[:,exponent+2])*(1000**exponent),width,color=tumcolors['tumblue'],edgecolor='none',log=1,zorder=1) #,label=r'|H$_{ad}$|$^{2}$' )
                            else:  ax.bar( habup[:,1]-mu,abs(habup[:,exponent+2])*(1000**exponent),width,color=tumcolors['tumblue'],edgecolor='none',zorder=1) #,label=r'|H$_{ad}$|$^{2}$' )
                            
                            ax.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                            ax.set_ylim(ycmin,ycmax)  #-1*HtoeV,1.5*HtoeV)
                            
                        if True:  #gamma stuff
                            ax11 = ax.twinx()
                            if plotgamma: ax11.plot( gammaup[:,0]-mu, gammaup[:,sigma],linewidth=1.0,label='up',linestyle='-',color=tumcolors['black'],zorder=0)
                    	    ax11.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                            ax11.set_ylim(ygmin,ygmax)  #-1*HtoeV,1.5*HtoeV)
               
               
               
                        
                        ax2 = fig1.add_subplot(212,sharex=ax)
                        ax2.axvline(x=0, ymin=0., ymax=1000.,linewidth=0.5,linestyle='--',color=tumcolors['black'],zorder=0)
                        ax2.axvline(x=Ecenter_dn, ymin=0., ymax=10.,linewidth=1,linestyle='-',color=tumcolors['tumred'],zorder=0)          
                        if use_resonance: ax2.axvline(x=resonance, ymin=0., ymax=10.,linewidth=1,linestyle='--',color=tumcolors['tumred'],zorder=0)          
##                       ax2.annotate(r'', xy=(0.95,0.15),xycoords='axes fraction',xytext=(0.95,0.55),textcoords='axes fraction',size=9,color="w",arrowprops=dict(arrowstyle="->",connectionstyle="arc3",color="k"), zorder=1)
                        #if shiftdos and annotate:  ax2.axvline(x=Ecenter, ymin=0., ymax=10.,linewidth=2,linestyle='--',color=tumcolors['tumred'])          
                   #     ax2.plot( dosdn[:,0],dosdn[:,1],linewidth=1.0,label='dn',color=tumcolors['mediumgray'],zorder=0) 
                    #    ax2.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                    #    ax2.set_ylim(0,ymax)  #-1*HtoeV,1.5*HtoeV)
                        
                        ax2.set_xlabel(r'E - $\epsilon_F$ [eV]')
                        
                        if True: #coupling things
                    
                            #ax3 = ax2.twinx()
##                          #coupling Hab in meV or meV**2
                            if uselog: ax2.bar( habdn[:,1]-mu, abs(habdn[:,exponent+2])*(1000),width,edgecolor='none',color=tumcolors['tumblue'],log=1,zorder=1) #,label=r'|H$_{ad}$|$^{2}$' )
                            else: ax2.bar( habdn[:,1]-mu, abs(habdn[:,exponent+2])*(1000**exponent) ,width,edgecolor='none',color=tumcolors['tumblue'],zorder=1)
                    
                            ax2.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                            ax2.set_ylim(ycmin,ycmax)  #-1*HtoeV,1.5*HtoeV)
                        
                        if True:  #gamma stuff
                            ax22 = ax2.twinx()
                	        #sigma=2
                            if plotgamma: ax22.plot( gammadn[:,0]-mu, gammadn[:,sigma],linewidth=1.0,label='up',linestyle='-',color=tumcolors['black'],zorder=0)   #energies are shifted.
                    	    ax22.set_xlim(xmin,xmax)  #-1*HtoeV,1.5*HtoeV)
                            ax22.set_ylim(ygmin,ygmax)  #-1*HtoeV,1.5*HtoeV)
                        
                        
                        if size=='LARGE':
                            ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
                            ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
                            ax2.xaxis.set_major_locator(ticker.MultipleLocator(2))
                            ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
                            #ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
                            #ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
                            #ax2.xaxis.set_major_locator(ticker.MultipleLocator(1))
                            #ax2.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
                        
                        elif size=='SMALL':
                            ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
                            ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
                            ax2.xaxis.set_major_locator(ticker.MultipleLocator(1))
                            ax2.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
 
 
                      #  if  ycmax <= 10:
                      #      ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
                      #      ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
                      #      ax2.yaxis.set_major_locator(ticker.MultipleLocator(2))
                      #      ax2.yaxis.set_minor_locator(ticker.MultipleLocator(1))
                      #  else:
                      #      ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
                      #      ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))
                      #      ax2.yaxis.set_major_locator(ticker.MultipleLocator(20))
                      #      ax2.yaxis.set_minor_locator(ticker.MultipleLocator(10))
                        
                        if  ygmax <= 10:
                            ax11.yaxis.set_major_locator(ticker.MultipleLocator(2))
                            ax11.yaxis.set_minor_locator(ticker.MultipleLocator(1))
                            ax22.yaxis.set_major_locator(ticker.MultipleLocator(2))
                            ax22.yaxis.set_minor_locator(ticker.MultipleLocator(1))
                        else:  #let this be automatic
                            ax11.yaxis.set_major_locator(ticker.MultipleLocator(20))
                            ax11.yaxis.set_minor_locator(ticker.MultipleLocator(5))
                            ax22.yaxis.set_major_locator(ticker.MultipleLocator(20))
                            ax22.yaxis.set_minor_locator(ticker.MultipleLocator(5))
                         
                        
                        ax.tick_params(
                                    axis='x',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    bottom='off',      # ticks along the bottom edge are off
                                    top='on',         # ticks along the top edge are off
                                    labelbottom='off') # labels along the bottom edge are off
                        ax.tick_params(
                                    axis='y',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    #bottom='off',      # ticks along the bottom edge are off
                                    left='on',
                                    right='off',
                                    #top='on',         # ticks along the top edge are off
                                    labelleft='on') # labels along the bottom edge are off
                        
                        #ax1.ticklabel_format(style='sci',axis='y')
                        ax11.tick_params(
                                    axis='x',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    bottom='off',      # ticks along the bottom edge are off
                                    right='off',
                                    top='off',         # ticks along the top edge are off
                                    labelbottom='off') # labels along the bottom edge are off
                        ax11.tick_params(
                                    axis='y',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    right='on',      # ticks along the bottom edge are off
                                    left='off',         # ticks along the top edge are off
                                    labelright='on') # labels along the bottom edge are off
                        
                        ax2.tick_params(
                                    axis='y',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    left='on',      # ticks along the bottom edge are off
                                    right='off',         # ticks along the top edge are off
                                    labelleft='on',
                                    labelright='off') # labels along the bottom edge are off
                        ax2.tick_params(
                                    axis='x',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    bottom='on',      # ticks along the bottom edge are off
                                    top='off',         # ticks along the top edge are off
                                    labelbottom='on',
                                    labeltop='off') # labels along the bottom edge are off
                        
                        ax22.tick_params(
                                    axis='x',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    bottom='off',      # ticks along the bottom edge are off
                                    top='off',         # ticks along the top edge are off
                                    labelbottom='off',
                                    labeltop='off') # labels along the bottom edge are off
                        ax22.tick_params(
                                    axis='y',          # changes apply to the x-axis
                                    which='both',      # both major and minor ticks are affected
                                    bottom='on',      # ticks along the bottom edge are off
                                    top='off',         # ticks along the top edge are off
                                    left='off',
                                    right='on',
                                    labelright='on',
                                    labelleft='off') # labels along the bottom edge are off
                       
                        #gamma axes
 
                    #    ax11.spines['left'].set_position(('outward', 30))      
                        # no x-ticks                 
                    #    ax11.xaxis.set_ticks([])
                        
                    #    ax33.spines['left'].set_position(('outward', 30))      
                        # no x-ticks                 
                    #    ax33.xaxis.set_ticks([])
 
 
                 #       ax11.tick_params(
                 #                   axis='y',          # changes apply to the x-axis
                 #                   which='both',      # both major and minor ticks are affected
                 #                   bottom='on',      # ticks along the bottom edge are off
                 #                   left='on',
                 #                   right='off',
                 #                   top='on',         # ticks along the top edge are off
                 #                   labelleft='on',
                 #                   labelright='off') # labels along the bottom edge are off
                 #       ax11.tick_params(
                 #                   axis='x',          # changes apply to the x-axis
                 #                   which='both',      # both major and minor ticks are affected
                 #                   bottom='on',      # ticks along the bottom edge are off
                 #                   #left='on',
                 #                   #right='off',
                 #                   top='on',         # ticks along the top edge are off
                 #                   labelbottom='off',
                 #                   labeltop='off') # labels along the bottom edge are off
                 #       ax33.tick_params(
                 #                   axis='y',          # changes apply to the x-axis
                 #                   which='both',      # both major and minor ticks are affected
                 #                   bottom='on',      # ticks along the bottom edge are off
                 #                   left='on',
                 #                   right='off',
                 #                   top='off',         # ticks along the top edge are off
                 #                   labelright='off',
                 #                   labelleft='on') # labels along the bottom edge are off
                 #       ax33.tick_params(
                 #                   axis='x',          # changes apply to the x-axis
                 #                   which='both',      # both major and minor ticks are affected
                 #                   bottom='on',      # ticks along the bottom edge are off
                 #                   #left='on',
                 #                   #right='off',
                 #                   top='on',         # ticks along the top edge are off
                 #                   labelbottom='off',
                 #                   labeltop='off') # labels along the bottom edge are off
                      
 
                        #ax.annotate('Ar4s', xy=(resonance,ymax*0.7),textcoords='data',size=9,color="k")
##                       ax.annotate(  r'$\mathbf{\ket{\uparrow}}$', xy=(0.8,0.5),size=15,textcoords='axes fraction',color="black")
##                       ax2.annotate(  r'$\mathbf{\ket{\downarrow}}$', xy=(0.8,0.5),size=15,textcoords='axes fraction',color="black")
                        
                      #  fig1.text(0.94,0.75, r'$\mathbf{\ket{\uparrow}}$',va='center',rotation=None,size=14)    #side
                      #  fig1.text(0.94,0.3, r'$\mathbf{\ket{\downarrow}}$',va='center',rotation=None,size=14) 
                        ax.annotate(r'$\mathbf{\ket{\uparrow}}$',xy=(1.09,0.55), textcoords='axes fraction', va='center',rotation=None,size=14,annotation_clip=False)     #inside
                        ax2.annotate(r'$\mathbf{\ket{\downarrow}}$',xy=(1.09,0.45), textcoords='axes fraction', va='center',rotation=None,size=14,annotation_clip=False) 
 
 
 
                        if plotgamma: ax11.annotate(r'$\Gamma$(E$_{\text{d}}$)', xy=(0.75,5),textcoords=('data','data'),size=9,color="k")
                        
                        
                        fig1.text(0.93,0.55,'$\Gamma$[fs$^{-1}$]',va='center',rotation='vertical') 
                        #fig1.text(0.13,0.55,'DOS [states/eV/cell]',va='center',rotation='vertical') 
                        if exponent==1: fig1.text(0.01,0.55,r'$\mathopen|\text{H}_{\text{da}}\mathclose|$ [meV]',va='center',rotation='vertical') 
                        elif exponent==2: fig1.text(0.05,0.55,r'$\mathopen|\text{H}_{\text{da}}\mathclose|^2$ [eV$^2$]',va='center',rotation='vertical') 
                     #   plt.suptitle('Acceptor DOS',fontsize=12)#+namestring,fontsize=10)
                        
                        ax2.invert_yaxis()
                        ax22.invert_yaxis()
                      #  ax33.invert_yaxis()
                       
                        syslabels=[r'$\textbf{Fe}$',r'$\textbf{Co}$',r'$\textbf{Ni}$','']
                        ax2.annotate(syslabels[sysindex], xy=(0.05,0.1),textcoords='axes fraction',size=12,color="k")
 
 
 
                        plt.subplots_adjust(hspace=0.0)
                        figname = 'method{}/gc{}_donorindex{}{}_{}'.format(mtag,exponent,donor_index_local,mtag,size)
                        if uselog==True: figname=figname+'log'
                        if plotgamma: figname = figname+'_g'
                        matplotlibhelpers.write(figname,transparent=True,write_info = False,write_png=True,write_pdf=True,write_eps=True)
                        plt.close(fig1)
            
            
        
        return None;


 
 


def plot_gc(mtag,sysindex,donor_index_local):



    #We want to show the dos and couplings and effective dos for a specific donor_index_local.
    #That means, first print the gamma test and couplings to files. Dos files already exit. Finally: just make the plot.
    #In the plot, show the donor energy level:  either the experimental level or the actual wd[donor_index_local].  Or just both!


    #dummy=1
    for mtag in [mtag]:# '_m2','_m1','_m3']:
        #make the sure the gamma files are there.
        #actually, we'll assume they are there.
        #gamma_test2(mtag,donor_index_local)   #let's do the gamma test around the fermi level (not around the donor, so we can see core state coupling as well).

        #sysindex=int(sys.argv[1])   #Fe , Co and Ni lifetimes.
        print('sysindex {}'.format(sysindex))
        if sysindex in [0,1,2]:
            errorbars =    [0.15, 0.15, 0.15]
            etimeup_list = [2.67, 3.24, 3.12] #fs   Feulner, PRL 2014.
            etimedn_list = [2.08, 2.63, 3.12]
            Ecenters_list = [2.97,3.11,3.14]
            annotate = True
            use_resonance = True
            resonance=Ecenters_list[sysindex]
            etimeup=etimeup_list[sysindex]
            etimedn=etimedn_list[sysindex]
            error = errorbars[sysindex]
               
        else:
            use_resonance = False
            resonance=0
            #Ecenter= 0    #dummy values, can do more elegantly later  (fill in actual donor energy level of future systems).
            etimeup= 0
            etimedn= 0
            error =  0
            annotate = False
 
        namestring='Lorentzian'
 
         
 
        mu=str(subprocess.check_output("grep 'Chemical potential (Fermi level):' ../aims.out  |  awk '{ print  $6}'  | tail -n 1", shell=True))
        mu=float(mu[:-3])
        print('mu is {}'.format(mu))
        
        #if len(sys.argv) > 2: donor_index_local=int(sys.argv[2])           #Ar4s has index 9 (level 10)
        #else: donor_index_local=9
        print('using donor index {}'.format(donor_index_local))
        
        wd_sorted_up = np.loadtxt('method{}/wd_sorted_up{}RAW'.format(mtag,mtag)+'.txt')[:,1]   #eV, unshifted.
        wd_sorted_dn = np.loadtxt('method{}/wd_sorted_dn{}RAW'.format(mtag,mtag)+'.txt')[:,1]
 
        Ecenter_up = wd_sorted_up[donor_index_local] - mu     #for method 3 there are multiple options... 
        Ecenter_dn = wd_sorted_dn[donor_index_local] - mu 
 
        print('Ecenter_up, Ecenter_dn {} {}'.format(Ecenter_up, Ecenter_dn))
 
        #sys.exit()
        #Now, before plot we have to extract the necessary data.
        #gamma_test(donor_index_local)   #let's do the gamma test around the fermi level (not around the donor, so we can see core state coupling as well).
        #sys.exit()
        #get_couplings(donor_index_local)  #obsolete. they are printed by the code.
 
 
 
        a = xy_plot()
        a.plot_gc_inner(mu,sysindex,Ecenter_up, Ecenter_dn,mtag,donor_index_local,use_resonance, resonance)
        print('finnished {}'.format(mtag))
    return None;


if __name__ == "__main__":
    plot_gc(mtag,sysindex,donor_index_local)
