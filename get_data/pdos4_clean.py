#!/usr/bin/env python
import os,sys
from os.path import basename
import pickle,cPickle
import numpy as np
from scipy.integrate import simps
from ase.io import read, write
from ase import Atom, Atoms
from Write import write_data
#import matplotlib.pyplot as plt

def split_name(folname):
    name_list=folname.split('O')
    met=name_list[0][:2]
    site=name_list[0][2:]
    return met, site
def supercell():
    atoms=read('opt.traj')
    atoms=atoms.copy()

def cal_feature():
	#if __name__ == '__main__':
	####unit transfer
	Ry_to_eV = 13.605698066
	#site_dict = {'110cuscusM':[25,1]} ##########attention: The index is for clean energy which is different with check_result file
	#site_dict is active site.  O_site_dict is adjacent oxygen
	site_dict = {'110cuscusM':(60), #+6.279600000000000d0 y
			 '110cuscusRu':(55),
			 '110bricusRu' : (24),
			 '111cuscusM'  : (27),
			 '111bricusRu' : (22),
			 '101cuscusM'  : (30), #-5.522673168855822d0 x
			 '101cuscusRu' : (26)  #+4.543300000000000d0 y
			}
	O_site_dict = {'110cuscusM':(21,26,27,58,59), #-1 -2  # bottom atom and coordinate atoms
			   '110cuscusRu':(52,28,29,58,59),
			   '110bricusRu': (21,26,27,58,59),
			   '111cuscusM'  : (18,23,24,25,26),
			   '111bricusRu' : (18,23,24,25,26),
			   '101cuscusM'  : (22,24,27,23,29), #-1 -2  
			   '101cuscusRu' : (25,27,29,23,24)  #-1 -2
			   }

	pathway=os.getcwd()
	folnames=os.listdir(pathway)
	folnames.sort()
	for folname in folnames:
	         list_name=['Ni', 'Cu' , 'Zn' , 'Ag' , 'Fe' , 'Co' , 'Ti' , 'W' , 'Mo' ,'Mn' , 'Ru' , 'Ir']
	         for startname in list_name:
                     judge_folder=False
                     if folname.startswith('{}'.format(startname)):
                        judge_folder=True
                        break
		 if judge_folder == False:
		    print('{} is not the working folder'.format(folname))
		    continue
		 if judge_folder == True:
		    print(folname)
		    os.chdir(folname)
		    met,site=split_name(folname)
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>1. Fermi level>>>>>>>>>>>>>>>>>>>>>>>>>
		    with open('{}/{}/esp.log/log'.format(pathway,folname)) as infile:
			 lines = infile.readlines()
			 for line in lines:
			     if 'Fermi energy' in line:
				 Ef = float(line[29:35])
			 print 'Ef', Ef
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>2. Work function>>>>>>>>>>>>>>>>>>>>>>>
		    if site in ['110cuscusM','110cuscusRu','110bricusRu']:
		       number1=72; number2=77
		    if site in ['111cuscusM','111bricusRu']:
		       number1=39; number2=44
		    if site in ['101cuscusM','101cuscusRu']:
		       number1=42; number2=47
		    with open('xsf_ionic_and_hartree_potential') as infile:
			 lines = infile.readlines()
		    nn = lines[number1].strip().split(' ')
		    nx,ny,nz = [int(x) for x in nn if x != '']
		   #print nx,ny,nz
		    dx = float(lines[2][4:15])/nx
		    x_values = []
		    for i in range(nx):
			x_values.append(i*dx)
		    dy = float(lines[3][19:30])/ny
		    y_values = []
		    for i in range(ny):
			y_values.append(i*dy)
		    dz = float(lines[4][33:])/nz
		    z_values = []
		    for i in range(nz):
			z_values.append(i*dz)
		#print 'dxyz', dx, dy, dz
		#collect potential data 
		    pot = []
		    for line in lines[number2:-2]:
			values = line.strip().split(' ')
			values = [float(x)*Ry_to_eV for x in values if x != '']
			pot += values
		#av   erage potential for work function calculation for z axis
		    av_pot = []
		    n=0
		    for i in range(0,nx*ny*nz,nx*ny):
			av_pot.append(sum(pot[n*nx*ny:(n+1)*nx*ny])/(nx*ny))
			n+=1
		#fi   nd the maximum potential far away from slab
		    d1=5   ### 4
		    d2=33  ### 23
		    z_fit_values = []
		    pot_fit_values = []
		    for z,p in zip(z_values,av_pot):
			if (z<d1) or (z>d2):
			    z_fit_values.append(z)
			    pot_fit_values.append(p)
		    Ev = max(pot_fit_values)
		    WF = Ev-Ef
		    print '{}o2'.format(met), 'WF', WF
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Density of state>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		#>>>>>>>>>>>>>>>>>>>>>>>>>3. d band center filling, 4. T2g filling
		#define site considered 
		#### for site in site_dict:
		    #n_atoms = len(site_dict[site]) 
		    #band = 250
		    with open('dos.pickle',"rb") as input_file:
			 dos_energies, dos_total, pdos = cPickle.load(input_file)
		    d_band_center = 0
		    d_band_filling = 0
		    eg_band_center = 0
		    eg_band_filling= 0
		    T2g_band_center =0
		    T2g_band_filling =0
		    if  site_dict[site]:
			atom_index = site_dict[site]
			print(atom_index)
		    
		#d band features
			states = 'd'
			if met == 'Ni' or met == 'Fe' or met == 'Co':
			    sum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1] #contains total pdos projected onto states (spin up infirst column, spin down in second column) followed by m-resolved pdos in following columns.
			else:
			    sum_pdos = pdos[atom_index][states][0] #contains total pdos projected onto states in first column followed by m-resolved pdos in following columns.
		    # intergrate on a defined region
			dos_energies_cutoff = np.array([])
			sum_pdos_cutoff = np.array([])
			n=0
			#number_row=len(sum_pdos)   # avoid index more then the maxmum of numbers
		       # plt.plot(sum_pdos,dos_energies)
		       # plt.show()
			for d,e in zip(sum_pdos,dos_energies):
			    #while n + 2 < number_row:
				if (e > 0) and ((sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01):
			       # if  (sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01:
				    #print met, atom_index, e
				    break
				else:
				    sum_pdos_cutoff = np.append(sum_pdos_cutoff, np.array([d]))
				    dos_energies_cutoff = np.append(dos_energies_cutoff, np.array([e]))
				    n+=1
			print (sum_pdos_cutoff), len(sum_pdos_cutoff)
		# d band center
			dbc = simps(sum_pdos_cutoff*dos_energies_cutoff,dos_energies_cutoff) / simps(sum_pdos_cutoff,dos_energies_cutoff)
		       # print(sum_pdos_cutoff)
			d_band_center += dbc #/n_atoms
			#print 'center', met, site, atom_index, dbc
			print 'center', met, site, atom_index, d_band_center
		# d band filling
			filled_pdos = []
			filled_dos_energies = []
			for d,e in zip(sum_pdos,dos_energies):
			    if e < 0:
				filled_pdos.append(d)
				filled_dos_energies.append(e)
			dbf = simps(filled_pdos,filled_dos_energies)
			d_band_filling += dbf #/n_atoms
			print 'd_band_filling', d_band_filling
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Eg  center  and filling (higher)
			states = 'd'
			if met == 'Ni' or met == 'Fe' or met == 'Co':
			   sum_pdos = pdos[atom_index][states][2] + pdos[atom_index][states][3]+pdos[atom_index][states][10] + pdos[atom_index][states][11]        
			else:
			   sum_pdos = pdos[atom_index][states][1] + pdos[atom_index][states][5]
		    # intergrate on a defined region
			dos_energies_cutoff = np.array([])
			sum_pdos_cutoff = np.array([])
			n=0
			#number_row=len(sum_pdos)   # avoid index more then the maxmum of numbers
		       # plt.plot(sum_pdos,dos_energies)
		       # plt.show()
			for d,e in zip(sum_pdos,dos_energies):
			    #while n + 2 < number_row:
				if (e > 0) and ((sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01):
			       # if  (sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01:
				    #print met, atom_index, e
				    break
				else:
				    sum_pdos_cutoff = np.append(sum_pdos_cutoff, np.array([d]))
				    dos_energies_cutoff = np.append(dos_energies_cutoff, np.array([e]))
				    n+=1
			print (sum_pdos_cutoff), len(sum_pdos_cutoff)
		# eg  band center
			dbc = simps(sum_pdos_cutoff*dos_energies_cutoff,dos_energies_cutoff) / simps(sum_pdos_cutoff,dos_energies_cutoff)
		       # print(sum_pdos_cutoff)
			eg_band_center += dbc #/n_atoms
			#print 'center', met, site, atom_index, dbc
			print 'eg center', met, site, atom_index, eg_band_center
		# eg   band filling
			filled_pdos = []
			filled_dos_energies = []
			for d,e in zip(sum_pdos,dos_energies):
			    if e < 0:
				filled_pdos.append(d)
				filled_dos_energies.append(e)
			dbf = simps(filled_pdos,filled_dos_energies)
			eg_band_filling += dbf #/n_atoms
			print 'eg_band_filling', eg_band_filling

		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>T2g   center and filling (lower)
			states = 'd'
			if met == 'Ni' or met == 'Fe' or met == 'Co':
			   sum_pdos = pdos[atom_index][states][4] + pdos[atom_index][states][5]+pdos[atom_index][states][6] + pdos[atom_index][states][7] + pdos[atom_index][states][8] + pdos[atom_index][states][9]
			else:
			   sum_pdos = pdos[atom_index][states][2] + pdos[atom_index][states][3] + pdos[atom_index][states][4]
		    # intergrate on a defined region
			dos_energies_cutoff = np.array([])
			sum_pdos_cutoff = np.array([])
			n=0
			#number_row=len(sum_pdos)   # avoid index more then the maxmum of numbers
		       # plt.plot(sum_pdos,dos_energies)
		       # plt.show()
			for d,e in zip(sum_pdos,dos_energies):
			    #while n + 2 < number_row:
				if (e > 0) and ((sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01):
			       # if  (sum_pdos[n-2]+sum_pdos[n-1]+sum_pdos[n]+sum_pdos[n+1]+sum_pdos[n+2])/5. < 0.01:
				    #print met, atom_index, e
				    break
				else:
				    sum_pdos_cutoff = np.append(sum_pdos_cutoff, np.array([d]))
				    dos_energies_cutoff = np.append(dos_energies_cutoff, np.array([e]))
				    n+=1
			print (sum_pdos_cutoff), len(sum_pdos_cutoff)
		# eg  band center
			dbc = simps(sum_pdos_cutoff*dos_energies_cutoff,dos_energies_cutoff) / simps(sum_pdos_cutoff,dos_energies_cutoff)
		       # print(sum_pdos_cutoff)
			T2g_band_center += dbc #/n_atoms
			#print 'center', met, site, atom_index, dbc
			print 'T2g center', met, site, atom_index, T2g_band_center
		# eg   band filling
			filled_pdos = []
			filled_dos_energies = []
			for d,e in zip(sum_pdos,dos_energies):
			    if e < 0:
				filled_pdos.append(d)
				filled_dos_energies.append(e)
			dbf = simps(filled_pdos,filled_dos_energies)
			T2g_band_filling += dbf #/n_atoms
			print 'T2g_band_filling', T2g_band_filling

		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Oxygen 2p band: 5. center and 6. filling
		    n_atoms = len(O_site_dict[site])
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
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>7. geometry >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		###bond length
		    atoms=read('opt.traj')
		    sum_distance=0 
		    n_atoms = len(O_site_dict[site])
		    if site=='110cuscusM' or site=='101cuscusM' or site=='101cuscusRu':
		       if site=='110cuscusM':
			  x0=atoms[site_dict[site]].position[0] 
			  y0=atoms[site_dict[site]].position[1]+ 6.27960000
			  z0=atoms[site_dict[site]].position[2]
		       if site=='101cuscusM':
			  x0=atoms[site_dict[site]].position[0]- 5.522673168855822
			  y0=atoms[site_dict[site]].position[1]
			  z0=atoms[site_dict[site]].position[2]
		       if site=='101cuscusRu':
			  x0=atoms[site_dict[site]].position[0]
			  y0=atoms[site_dict[site]].position[1]+ 4.5433000000000
			  z0=atoms[site_dict[site]].position[2]
		       for j in range(0,3):
			   distance_i=atoms.get_distance(site_dict[site],O_site_dict[site][j])
			   sum_distance=sum_distance+distance_i
		       for k in [-1,-2]:
			   x1,y1,z1=atoms[O_site_dict[site][k]].position[0],atoms[O_site_dict[site][k]].position[1],atoms[O_site_dict[site][k]].position[2]
			   distance_i=np.sqrt((x1-x0)**2+(y1-y0)**2+(z1-z0)**2)
			   sum_distance=sum_distance+distance_i
		    else:
		       for i in range(len(O_site_dict[site])):    
			   distance_i=atoms.get_distance(site_dict[site],O_site_dict[site][i]) 
			   sum_distance=sum_distance+distance_i
		    avr_distance=sum_distance/n_atoms   
		    print 'length:', avr_distance
		    write_data('/naslx/projects/pr47fo/ge39luv2/data/feature',folname,Ef,WF,d_band_center,d_band_filling,eg_band_center,eg_band_filling,T2g_band_center,T2g_band_filling,p_band_center,p_band_filling,avr_distance)
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>8. bader charge>>>>>>>>>>>>>>>>>>>>>>>
		    os.chdir(pathway)


			     
			
		    
		    
		    
		    










