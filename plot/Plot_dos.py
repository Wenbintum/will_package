#!/usr/bin/env python
import os,sys
import matplotlib.pyplot as plt

def plot_dos(x_list,y_list,*args):
    fig = plt.figure(figsize=(5., 5.))
    plt.plot(x_list, y_list, '-')
    x_cor = 1.5
    pyplot.text(x_cor,9,'band center: %.2f'%center)
    pyplot.ylim([-10,15])
    pyplot.savefig(''.pdf'.format(**locals()), dpi=300)


