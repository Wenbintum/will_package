#!/usr/bin/env python

import os,sys
import matplotlib.pyplot as pyplot

def split_name(folname):
    name_list=folname.split('O')
    met=name_list[0][:2]
    site=name_list[0][2:]
    return met, site

def plot_O2p():
    pathway=os.getcwd()
    folname=basename('{}'.format(pathway))
    met,site=split_name(folname)
    O_site_dict = {'110cuscusM':(21,26,27,58,59), #-1 -2  # bottom atom and coordinate atoms
		   '110cuscusRu':(52,28,29,58,59),
		   '110bricusRu': (21,26,27,58,59),
		   '111cuscusM'  : (18,23,24,25,26),
		   '111bricusRu' : (18,23,24,25,26),
		   '101cuscusM'  : (22,24,27,23,29), #-1 -2  
		   '101cuscusRu' : (25,27,29,23,24)  #-1 -2
		   }

    p_band_center = 0
    p_band_filling = 0
    for atom_index in O_site_dict[site]:
	    states = 'p'
	    if met == 'Ni' or met == 'Fe' or met == 'Co':
	       psum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1] #contains total pdos projected onto states (spin up in first column, spin down in second column) followed by m-resolved pdos in following columns.
	    else:
		psum_pdos = pdos[atom_index][states][0] #contains total pdos projected onto states in first column followed by m-resolved pdos in following columns.
	    #integrate up to cutoff
	    pdos_energies_cutoff=np.array([])
	    psum_pdos_cutoff=np.array([])
	    n=0
	    for d,e in zip(psum_pdos,dos_energies):
		    if (e > 0) and ((psum_pdos[n-2]+psum_pdos[n-1]+psum_pdos[n]+psum_pdos[n+1]+psum_pdos[n+2])/5. < 0.01):
			#print met, atom_index, e
			break
		    else:
			psum_pdos_cutoff = np.append(psum_pdos_cutoff, np.array([d]))
			pdos_energies_cutoff = np.append(pdos_energies_cutoff, np.array([e]))
			n+=1
	    #2p-band center
	    pbc = simps(psum_pdos_cutoff*pdos_energies_cutoff,pdos_energies_cutoff) / simps(psum_pdos_cutoff,pdos_energies_cutoff)
	    p_band_center += pbc/n_atoms
	    #print 'center', met, site, atom_index, dbc
	    #print '2p center', met, site, atom_index, p_band_center
	    #2p-band filling
	    pfilled_pdos = []
	    pfilled_dos_energies = []
	    for d,e in zip(psum_pdos,dos_energies):
		if e < 0:
		    pfilled_pdos.append(d)
		    pfilled_dos_energies.append(e)
	    p_band_filling += (simps(pfilled_pdos,pfilled_dos_energies))/n_atoms ### /n_atoms after loop equal = 3*atoms/3 avr
    print '2p center', met, site, atom_index, p_band_center
    print '2p_band_filling', p_band_filling


