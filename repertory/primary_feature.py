import pickle,cPickle
import numpy as np
from scipy.integrate import simps
import os,sys
import matplotlib.pyplot as plt
from ase.io import read,write
from ase import Atoms,Atom
from scipy.special import sph_harm
import warnings
#root 
from parameter import PM
from io_file import File_oprate

def Get_energy(pathway,folname):
    energy=0
    energy_list=[]
    with open('{}/{}/esp.log/log'.format(pathway,folname),'r') as infile:
        lines=infile.readlines()
        for line in lines:
            if line.startswith('!    total energy'):
                energy_list.append(line.split()[-2])
    energy=float(energy_list[-1])
    return energy


def Formation_energy(pathway,folname,rutile_type):
    E_doped = Get_energy(pathway,folname)
    met,site=File_oprate.split_name(folname)
    if rutile_type == 'Ruo2':
        name = 'Ru'
    if rutile_type == 'Iro2':
        name = 'Ir'
    E_pure = Get_energy(pathway,name+site)
    E_bulk_metal = PM.E_bulk_metal[met]
    E_bulk_oxide = PM.E_bulk_oxide[rutile_type]
    E_O2 = PM.E_O2
    formation_energy = (E_doped - E_pure - 2*E_bulk_metal + 
                        2* E_bulk_oxide - 2*E_O2)/2*PM.Ry_to_eV
    return round(formation_energy,4) 

#1-5
class Geometry(object):

    def __init__(self,site):
        self.site=site

    def Variable(self):
        #read trajectory and extend supercell
        atoms=read('opt.traj')
        copy_coefficent = (1,1,1)
        if self.site[:3] == '110' or self.site[:3] == '111':
            copy_coefficent = (2,2,1)
        if self.site[:3] == '101' or self.site[:3] == '100':
            copy_coefficent = (3,3,1)
        atoms=atoms*copy_coefficent
        self.atoms=atoms

    def Nearest_metal(self):
        distance_list=[]
        for i in PM.nearest_metal_dic[self.site][1:]:
            distance_list.append(self.atoms.get_distance(PM.nearest_metal_dic[self.site][0],i))
        distance_list.sort()
        nearest_1 = distance_list[0]
        nearest_2 = distance_list[1]
        nearest_3 = distance_list[2]
        return round(nearest_1,4), round(nearest_2,4), round(nearest_3,4)

    def Site_1fold(self):
        distance_list=[]
        if self.site[:3] == '111':
            distance_list = ['inf']
            return distance_list
        else:
            for i in PM.site_1foldO_dic[self.site][1:]:
                distance_list.append(self.atoms.get_distance(PM.site_1foldO_dic[self.site][0],i))
            distance_list.sort()
            return round(distance_list[0],4)

    def Relative_distance(self):
        distance_list=[]
        for i in PM.relative_dis_dic[self.site][1:]:
            distance_list.append(self.atoms.get_distance(PM.relative_dis_dic[self.site][0],i))
        distance_list.sort()
        return round(distance_list[0],4)

    def Spherical_hamonics(self):   #l= 1,2,3,4,5,6
        O_coordinate=[]
        #determine the coordinate of nearby Oxygen atom, put into a 5x3 list
        for i in range(1,len(PM.hamonics_dic[self.site])):
            O_coordinate.extend([self.atoms[PM.hamonics_dic[self.site][i]].position[0],
                                 self.atoms[PM.hamonics_dic[self.site][i]].position[1],
                                 self.atoms[PM.hamonics_dic[self.site][i]].position[2]])           
        O_coordinate = np.reshape(O_coordinate,(5,3))
        #get vector by Oxygen list minus active site coordinate
        M_coordinate = [ self.atoms[PM.hamonics_dic[self.site][0]].position[0],
                         self.atoms[PM.hamonics_dic[self.site][0]].position[1],
                         self.atoms[PM.hamonics_dic[self.site][0]].position[2] ]
        vec2_multi = O_coordinate - M_coordinate
        #compute phi: polar angle  and   theta: azimuth angle
        phi_list=[]
        theta_list=[]
        for i in range(0,5):
            r=np.sqrt(vec2_multi[i][0]**2 + vec2_multi[i][1]**2 + vec2_multi[i][2]**2)
            phi=np.arccos(vec2_multi[i][2]/r)
            theta=np.arctan2(vec2_multi[i][1],vec2_multi[i][0])
            if theta  < 0:
                theta=theta+2*np.pi
            phi_list.append(phi)
            theta_list.append(theta)
        #phi_list=[round(i*180/np.pi,2) for i in phi_list]
        #compute spherical hamonics
        Q_l_list=[]
        for l in range(1,7):    #l=1-6
            Q_lms=0
            for m in range(-l,l+1):
                Y_lms=0
                for i in range(0,5):
                    Y_lm= sph_harm(m,l,theta_list[i],phi_list[i])
                    Y_lms += Y_lm
                Q_lm=Y_lms/5 #length of oxygen_list
                Q_lms=Q_lms+ abs(Q_lm)**2
            Q_l=np.sqrt(4*np.pi/(2*l+1)*Q_lms)
            Q_l_list.append(round(Q_l,4))
        return Q_l_list[0], Q_l_list[1], Q_l_list[2], Q_l_list[3], Q_l_list[4], Q_l_list[5]


def Fermi_level(pathway,folname):
    """
    Input:
    - pathway:
    - folname:
    - file: log file of quantum-espresso
    Output:
    - Ef
    """
    with open('{}/{}/esp.log/log'.format(pathway,folname)) as infile:
        lines=infile.readlines()
    for line in lines:
        if 'Fermi energy' in line:
            Ef = float(line[29:35])
    return round(Ef,4)

#6
def Work_function(site,Ef,pathway,filename='xsf_ionic_and_hartree_potential'):
    """
    Input:
    - Site: representation of active site obatained from splitting folder name
    - Ef: fermi level
    - file: xsf_ionic_and_hartree_potential (grid  and potential)
    Output: 
    - WF
    """
    #determine the extracted lines in xsf_ionic_and hartree_potential file
    list110=['110cuscusM','110cuscusRu','110bricusRu']
    list111=['111cuscusM','111bricusRu']
    list101=['101cuscusM','101cuscusRu']
    list100=['100cuscusM','100cuscusRu']
    if site in list110:
        number1=72; number2=77
    if site in list111:
        number1=39; number2=44
    if site in list101:
        number1=42; number2=47
    if site in list100:
        number1=54; number2=59
    #determine the numbers of grid
    with open('{}/{}'.format(pathway,filename)) as infile:
        lines=infile.readlines()
    nn = lines[number1].strip().split(' ')
    nx,ny,nz=[int(x) for x in nn if x != '']
    #determine step of grid and put the value of each x into list
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
    #collect potential data
    pot = []
    for line in lines[number2:-2]:
        values = line.strip().split(' ')
        values = [float(x)*PM.Ry_to_eV for x in values if x != '']
        pot += values
    #average potential for work function calculation for z axis
    av_pot = []
    n=0
    for i in range(0,nx*ny*nz,nx*ny):
        av_pot.append(sum(pot[n*nx*ny:(n+1)*nx*ny])/(nx*ny))
        n+=1
    #find the maximum potential far away from slab
    d1=5   # 4
    d2=33  # 23
    z_fit_values = []
    pot_fit_values = []
    for z,p in zip(z_values,av_pot):
        if (z<d1) or (z>d2):
            z_fit_values.append(z)
            pot_fit_values.append(p)
    Ev = max(pot_fit_values)
    WF = Ev-Ef
    return round(WF,4)  

#7-9
def Bader_charge(met,site,rutile_type):
    os.system('cp /p/project/lmcat/wenxu/scripts/bader/pre.cri .')
    os.system('cp /p/project/lmcat/wenxu/scripts/bader/run.cri .')
    os.system('cp /p/project/lmcat/wenxu/scripts/bader/run_bader.sh .')
    os.system('cp xsf_charge_density charge_density.xsf')
    if rutile_type == 'Ruo2':
        os.system('sed -i "s/zpsp Ru 16 O 6/zpsp Ru 16 O 6 {} {}/g" pre.cri'.format(met,PM.charge_list[met]))
    elif rutile_type == 'Iro2':
        os.system('sed -i "s/zpsp Ru 16 O 6/zpsp Ir 9 O 6 {} {}/g" pre.cri'.format(met,PM.charge_list[met]))
    else:
        warnings.warn('PLEASE input the rutile type')  
        sys.exit()
    os.system('bash run_bader.sh')
    atom_index = PM.site_dict[site]
    metal_index = PM.surface_metal_dic[site]
    oxygen_index = PM.O_site_dict[site]
    aver_metal=0
    aver_oxygen=0
    with open('output','r') as input_file:
        lines=input_file.readlines()
        n=2
        for line in lines:
            n=n+1
            if line.startswith('* Integrated atomic properties'):
                bader_charge=float(lines[n+1+atom_index].split()[-1])
                for metalindex in metal_index:
                    aver_metal=float(aver_metal)+float(lines[n+1+metalindex].split()[-1])
                aver_metal = aver_metal/len(metal_index)
                for oxygenindex in oxygen_index:
                    aver_oxygen=float(aver_oxygen)+float(lines[n+1+oxygenindex].split()[-1])
                aver_oxygen = aver_oxygen/len(oxygen_index)
                break
    os.system('rm run.cri')
    os.system('rm charge_density.xsf')
    os.system('rm run_bader.sh')
    os.system('rm rhof.cube')
    os.system('rm preoutput')
    os.system('rm output')
    return round(bader_charge,4), round(aver_metal,4), round(aver_oxygen,4)

#10-15
def Atomic_feature(met,site,rutile_type):
    if site[-2:] == 'Ru':
        if rutile_type == 'Ruo2':
            PE =  PM.atom_descriptor['Ru'][0]
            IE =  PM.atom_descriptor['Ru'][1] 
            EA =  PM.atom_descriptor['Ru'][2]
            Radius = PM.atom_descriptor['Ru'][3]
            Vad2 = PM.atom_descriptor['Ru'][4]
            bulk_radius = PM.atom_descriptor['Ru'][5]
        if rutile_type == 'Iro2':
            PE =  PM.atom_descriptor['Ir'][0]
            IE =  PM.atom_descriptor['Ir'][1] 
            EA =  PM.atom_descriptor['Ir'][2]
            Radius = PM.atom_descriptor['Ir'][3]
            Vad2 = PM.atom_descriptor['Ir'][4]
            bulk_radius = PM.atom_descriptor['Ir'][5]
    if site[-1:] == 'M':
        PE =  PM.atom_descriptor[met][0]
        IE =  PM.atom_descriptor[met][1] 
        EA =  PM.atom_descriptor[met][2]
        Radius = PM.atom_descriptor[met][3]
        Vad2 = PM.atom_descriptor[met][4]
        bulk_radius = PM.atom_descriptor[met][5]
    return PE, IE, EA, Radius, Vad2, bulk_radius

class DOS_extract(object):

    def __init__(self,site,met,pathway):
        self.site=site
        self.met=met
        self.pathway=pathway
        #index of active site
        self.atom_index=PM.site_dict[site]
        # self.sum_pdos
    def dos_collect(self):
        """
        Input:
        - file: dos.pickle file
        Output:
        - dos_energies: energy window (y axis)
        - dos_total:   numbers of density states (x axis)
        - pdos: density state of each atom and each orbital
        """
        with open('{}/dos.pickle'.format(self.pathway),"rb") as input_file:
            dos_energies, dos_total, pdos = cPickle.load(input_file)
        return dos_energies, dos_total, pdos

    def Max_d_band(self):
        pdos=self.dos_collect()[2]
        dos_energies=self.dos_collect()[0]

        states = 'd'
        if  self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
		    sum_pdos = pdos[self.atom_index][states][0] + pdos[self.atom_index][states][1]
        else:
		    sum_pdos = pdos[self.atom_index][states][0] 
        #find the index of maximum value
        max_index=np.where(sum_pdos == np.amax(sum_pdos))
        Max_d_energy= dos_energies[max_index]
        return round(float(Max_d_energy[0]),4)    ###if same value exists in Max_d_energy list then return the first one

    def D_band_center(self):
        """
        Input:
        - pdos: projected density state (come from function dos_collect)
        - site_dict: the index of ative atom (address PM library )
        - states: 'd'
        Output:
        - sef.sum_pdos: global variable
        - dbc : d band center
        """
        dbc=0
        pdos=self.dos_collect()[2]
        dos_energies=self.dos_collect()[0]
        #collect dos
        states = 'd'
        #contains total pdos projected onto states (spin up infirst column, spin down in second column) followed by m-resolved pdos in following columns.
        if  self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
		    sum_pdos = pdos[self.atom_index][states][0] + pdos[self.atom_index][states][1]
        else:
		    sum_pdos = pdos[self.atom_index][states][0] 
        dbc = simps(sum_pdos*dos_energies,dos_energies) / simps(sum_pdos,dos_energies)
        #plt.plot(dos_energies,sum_pdos)
        #plt.show()
        return round(dbc,4), sum_pdos
        
    def D_band_width(self):
        sum_pdos=self.D_band_center()[1]
        dos_energies=self.dos_collect()[0]
        dbc=self.D_band_center()[0]
        d_band_mom2 = simps(sum_pdos*np.power(dos_energies-dbc,2),dos_energies)/simps(sum_pdos,dos_energies)
        dbw=np.sqrt(d_band_mom2)
        return round(dbw,4)
    
    def D_band_skewness(self):
        sum_pdos=self.D_band_center()[1]
        dos_energies=self.dos_collect()[0]
        dbc=self.D_band_center()[0]
        dbw=self.D_band_width()
        d_band_mom3 = simps(sum_pdos*np.power(dos_energies-dbc,3),dos_energies)/simps(sum_pdos,dos_energies)
        dbs=d_band_mom3/np.power(dbw,3)
        return round(dbs,4)

    def D_band_kutosis(self):
        sum_pdos=self.D_band_center()[1]
        dos_energies=self.dos_collect()[0]
        dbc=self.D_band_center()[0]
        dbw=self.D_band_width()
        d_band_mom4 = simps(sum_pdos*np.power(dos_energies-dbc,3),dos_energies)/simps(sum_pdos,dos_energies)
        dbk=d_band_mom4/np.power(dbw,4)
        return round(dbk,4)

    def D_band_filling(self):
        """
        Output:
        - dbf: d occupied filling
        - fraction: the fraction of unoccupied orbital / entire orbital
        """
        filled_pdos = []
        filled_dos_energies = []
        dos_energies=self.dos_collect()[0]
        sum_pdos=self.D_band_center()[1]

        for d,e in zip(sum_pdos,dos_energies):
			if e < 0:
			    filled_pdos.append(d)
			    filled_dos_energies.append(e)
        #d occupied filling
        dbf = simps(filled_pdos,filled_dos_energies)
        #fraction of unoccupied filling
        dbf_entire = simps(sum_pdos,dos_energies)
        fraction= 1. - (dbf/dbf_entire)
        return round(dbf,4),  round(fraction,4)

    def D_un_band_center(self):  #if the fraction of un_band is too small, which might be annoying things.
        sum_pdos=self.D_band_center()[1]
        dos_energies=self.dos_collect()[0]

        #define the region  energy > 0
        dos_energies_un=np.array([])
        sum_pdos_un=np.array([])
        for d,e in zip(sum_pdos,dos_energies):
            if e < 0:
                continue
            else:
                sum_pdos_un = np.append(sum_pdos_un, np.array([d]))
                dos_energies_un = np.append(dos_energies_un, np.array([e]))
        
        d_un_band_center=simps(sum_pdos_un*dos_energies_un,dos_energies_un) / simps(sum_pdos_un,dos_energies_un)
        return round(d_un_band_center,4)

    def Eg_band_center(self):
        pdos=self.dos_collect()[2]
        dos_energies=self.dos_collect()[0]

        states = 'd'
        if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
            sum_pdos = ( pdos[self.atom_index][states][2]  + pdos[self.atom_index][states][3]
                        +pdos[self.atom_index][states][10] + pdos[self.atom_index][states][11] )        
        else:
            sum_pdos = pdos[self.atom_index][states][1] + pdos[self.atom_index][states][5]
        eg_band_center = simps(sum_pdos*dos_energies,dos_energies) / simps(sum_pdos,dos_energies)
        return round(eg_band_center,4), sum_pdos

    def Eg_band_filling(self):
        filled_pdos = []
        filled_dos_energies = []
        sum_pdos = self.Eg_band_center()[1]
        dos_energies=self.dos_collect()[0]

        for d,e in zip(sum_pdos,dos_energies):
            if e < 0:
                filled_pdos.append(d)
                filled_dos_energies.append(e)
        eg_band_filling = simps(filled_pdos,filled_dos_energies)
        return round(eg_band_filling,4)

    def T2g_band_center(self):
        pdos=self.dos_collect()[2]
        dos_energies=self.dos_collect()[0]

        states = 'd'
        if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
            sum_pdos = ( pdos[self.atom_index][states][4] + pdos[self.atom_index][states][5] + pdos[self.atom_index][states][6] 
                       + pdos[self.atom_index][states][7] + pdos[self.atom_index][states][8] + pdos[self.atom_index][states][9] )
        else:
            sum_pdos = pdos[self.atom_index][states][2] + pdos[self.atom_index][states][3] + pdos[self.atom_index][states][4]
        T2g_band_center = simps(sum_pdos*dos_energies,dos_energies) / simps(sum_pdos,dos_energies)
        return round(T2g_band_center,4), sum_pdos

    def T2g_band_filling(self):
        filled_pdos = []
        filled_dos_energies = []
        sum_pdos = self.T2g_band_center()[1]
        dos_energies=self.dos_collect()[0]

        for d,e in zip(sum_pdos,dos_energies):
            if e < 0:
                filled_pdos.append(d)
                filled_dos_energies.append(e)
        T2g_band_filling = simps(filled_pdos,filled_dos_energies)
        return round(T2g_band_filling,4)
    
    def Dos_fermi(self):
        Eint = 0.1
        Emin = -Eint
        Emax = Eint
        d_dos_EF = 0
        sp_dos_EF = 0
        dos_energies=self.dos_collect()[0]
        pdos=self.dos_collect()[2]

        states = 'd'
        if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
            sum_pdos = pdos[self.atom_index][states][0] + pdos[self.atom_index][states][1]
        else:
            sum_pdos = pdos[self.atom_index][states][0]
        EF_pdos = []
        for e,d in zip(dos_energies,sum_pdos):
            if Emin < e < Emax:
                EF_pdos.append(d)
        d_dos_EF= np.average(EF_pdos)

        states = 's'
        if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
            s_pdos = pdos[self.atom_index][states][0] + pdos[self.atom_index][states][1]
        else:
            s_pdos = pdos[self.atom_index][states][0]
        states = 'p'
        if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
            p_pdos = pdos[self.atom_index][states][0] + pdos[self.atom_index][states][1]
        else:
            p_pdos = pdos[self.atom_index][states][0]
        sp_pdos = s_pdos + p_pdos
        sp_EF_pdos = []
        for e,d in zip(dos_energies,sp_pdos):
            if Emin < e < Emax:
                sp_EF_pdos.append(d)
        sp_dos_EF = np.average(sp_EF_pdos)
        return round(d_dos_EF + sp_dos_EF, 4)

    def O2p_band_center(self):
        p_band_center = 0
        pdos=self.dos_collect()[2]
        dos_energies=self.dos_collect()[0]
        n_atoms=len(PM.O_site_dict[self.site])
        for atom_index in PM.O_site_dict[self.site]:
            states='p'
            if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
                psum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1]
            else:
                psum_pdos = pdos[atom_index][states][0]
            pdos_collect = []
            pdos_energies_collect = []
            for d,e in zip(psum_pdos,dos_energies):
                pdos_collect=np.append(pdos_collect,np.array([d]))
                pdos_energies_collect=np.append(pdos_energies_collect,np.array([e]))
            pbc = simps(pdos_collect*pdos_energies_collect,pdos_energies_collect) / simps(pdos_collect,pdos_energies_collect)
            p_band_center += pbc        
        p_band_center = p_band_center/n_atoms
        return round(p_band_center,4)

    def O2p_band_filling(self):
        p_band_filling=0
        pdos=self.dos_collect()[2]
        dos_energies = self.dos_collect()[0]
        n_atoms=len(PM.O_site_dict[self.site])
        
        for atom_index in PM.O_site_dict[self.site]:
            states='p'
            if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
                psum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1]
            else:
                psum_pdos = pdos[atom_index][states][0]
            pfilled_pdos = []
            pfilled_dos_energies = []
            for d,e in zip(psum_pdos, dos_energies):
                if e < 0:
                    pfilled_pdos.append(d)
                    pfilled_dos_energies.append(e)
            pbf=(simps(pfilled_pdos,pfilled_dos_energies))
            p_band_filling += pbf
        p_band_filling = p_band_filling/n_atoms
        return round(p_band_filling,4)

    def Max_2p_band(self):
        Max_2p_band=0
        pdos=self.dos_collect()[2]
        dos_energies = self.dos_collect()[0]
        n_atoms=len(PM.O_site_dict[self.site])

        for atom_index in PM.O_site_dict[self.site]:
            states='p'
            if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
                psum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1]
            else:
                psum_pdos = pdos[atom_index][states][0]
            max_index=np.where(psum_pdos == np.amax(psum_pdos))
            Max_2p_energy= dos_energies[max_index]
            Max_2p_band += float(Max_2p_energy[0])
        Max_2p_band = Max_2p_band/n_atoms
        #plt.plot(dos_energies,psum_pdos)
        #plt.show()
        return round(Max_2p_band,4)

    def O2p_fermi(self):
        Eint = 0.1
        Emin = -Eint
        Emax = Eint
        O2p_dos_EF = 0
        dos_energies=self.dos_collect()[0]
        pdos=self.dos_collect()[2]
        n_atoms=len(PM.O_site_dict[self.site])
        for atom_index in PM.O_site_dict[self.site]:
            states='p'
            if self.met == 'Ni' or self.met == 'Fe' or self.met == 'Co':
                psum_pdos = pdos[atom_index][states][0] + pdos[atom_index][states][1]
            else:
                psum_pdos = pdos[atom_index][states][0]
            O2p_EF_collect=[]
            for e,d in zip(dos_energies,psum_pdos):
                if Emin < e < Emax:
                    O2p_EF_collect.append(d)
            aver_EF= np.average(O2p_EF_collect)
            O2p_dos_EF += aver_EF
        O2p_dos_EF = O2p_dos_EF/n_atoms
        return round(O2p_dos_EF,4)

