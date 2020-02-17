#!/usr/bin/env python
import os,sys
import numpy as np
from ase import Atoms,Atom
from ase.io import read,write

class Adsorbate:
      ads_indices =  {   #(active_site,ending_atoms,others_adsatoms,others) 
                      'O': {'110cuscusM'  : (62,26),
                            '110cuscusRu' : (58,31),
                            '110bricusRu' : (26,1),
                            '111cuscusM'  : (28,27),
                            '111bricusRu' : (28,27),
                            '101cuscusM'  : (29,0),
                            '101cuscusRu' : (30,3)
                            },

                      'OH': {'110cuscusM' : (60,62,63),
                            '110cuscusRu' : (55,62,63),
                            '110bricusRu' : (24,62,63),
                            '111cuscusM'  : (27,29,30),
                            '111bricusRu' : (28,27),
                            '101cuscusM'  : (30,32,33),
                            '101cuscusRu' : (26,32,33)
                            },

                      'OOH': {'110cuscusM'  : (26,1),
                            '110cuscusRu' : (58,31),
                            '110bricusRu' : (26,1),
                            '111cuscusM'  : (28,27),
                            '111bricusRu' : (28,27),
                            '101cuscusM'  : (29,0),
                            '101cuscusRu' : (30,3)
                            }
                      }
  
      def __init__(self,kind,site):
          self.kind=kind
          self.site=site
          self.ads_indice=self.ads_indices[self.kind][self.site]
      def cal_angle(self):
          #ads_indice = self.ads_indices[self.kind][self.site]    ###self.ads_indices
          vector1=atoms[self.ads_indice[1]].position-atoms[self.ads_indice[0]].position
          vector2=np.array([0,0,1])
          L1=np.sqrt(vector1.dot(vector1))
          L2=np.sqrt(vector2.dot(vector2))
          cos_angle=vector1.dot(vector2)/(L1*L2)
          angle=90-np.arccos(cos_angle)*360/2/np.pi     ###radian*360/2/np.pi=angle
          return round(angle,2) #,self.ads_indice[1],self.ads_indice[0]
      def cal_bond(self):
          ## the first two index are used to cal length
          return round(atoms.get_distance(self.ads_indice[1],self.ads_indice[0]),3)
      def cal_coordinat(self):
          indexs=[]
          symbols=[]
          distances=[]
          count=0
          for index in range(len(atoms)):
              length=atoms.get_distance(self.ads_indice[1],index)
              if length <= 2.5 and length != 0.0:
                 count+=1
                 indexs.append(index)  
                 symbols.append(atoms[index].symbol)
                 distances.append(round(length,3))    ###round(a,3) specify digit
          sum_list=list(zip(symbols,distances))
          dictionary=dict(zip(indexs,sum_list))
          return count, dictionary
     # def cal_move(self):

def read_data(output_name):
    with open('{}'.format(output_name),'r') as input_file:
         lines=input_file.readlines()
         if len(lines) < 1:
            line=0
         else:
            line =lines[-1].split()
         return line

def write_data(filename,folname,line,pathway,state,judge_spin,bond_calculation,angle_calculation,coordinate_calculation):
    os.chdir('/naslx/projects/pr47fo/ge39luv2/data')
    with open('{}'.format(filename),'a') as output_file:   ####mode 'a' means add content at the end of file
         output_file.write(' {0:17}{1:16}{2:8}{3:16}{4:8}{5:4}{6:7}{7:25}\n'.format(folname,line[-2],line[-1],state,judge_spin,bond_calculation,angle_calculation,coordinate_calculation))
         os.chdir(pathway)

def check_spin(strings1,strings2,pathway):
    judge_spin='NoSpin'
    with open('{}/pw.inp'.format(pathway), 'r') as input_file:
         for line in input_file:
             if strings1 in line:
                with open('{}/log'.format(pathway), 'r') as input_file2:
                     for line2 in input_file2:
                         if strings2 in line2:
                            judge_spin='Spin'
                            break
    return judge_spin


def split_name(folname):
    site=folname.split('O')[0]
    if folname.split('O')[1]==" ":
       kind='O'
    elif folname.split('O')[1]=="H":
         kind='OH'
    elif folname.split('O')[1]=="OH":
         kind='OOH'
    return kind,site 

pathway=os.getcwd()
folnames=os.listdir(pathway)
folnames.sort()
for folname in folnames:
    os.chdir(folname)
    output_name=False
    ads_object=0
    angle_calculation=0
    bond_calculation=0
    coordinate_calculation=0
    try:
        atoms=read('opt.traj')
        ads_object=Adsorbate(*split_name(folname[2:]))
        angle_calculation=ads_object.cal_angle()
        bond_calculation=ads_object.cal_bond()
        coordinate_calculation=ads_object.cal_coordinat()
    except:
        print(folname +' without 1 relaxzation')

    if os.path.exists('2x1x4.log'):
       output_name='2x1x4.log'
       line=read_data('2x1x4.log')
       if line==0:
           state='SCF failed'
           line=[0.000000,0.000000]
       else:
           if float(line[-1]) <= 0.03:
              state='conver success'
           else:
               state='force failed'
    if os.path.exists('relax.log'):
       output_name='relax.log'
       line=read_data('relax.log')
       if line==0:
           state='SCF failed'
           line=[0.000000,0.000000]
       else:
           if float(line[-1]) <= 0.03:
              state='conver success'
           else:
               state='force failed'
    if not output_name:
       state='log inexist'
       line=[0,0]
    #write('{}T.png'.format(folname), atoms)
    #write('{}S.png'.format(folname), atoms, rotation='-90x')
    #os.system('mv *.png /naslx/projects/pr47fo/ge39luv2/structure/picture')
    try:
        judge_spin=check_spin('nspin','SPIN','{}/{}/esp.log'.format(pathway,folname))
    except:
        try:
            judge_spin=check_spin('nspin','SPIN','{}/{}'.format(pathway,folname))
        except:
            judge_spin='NoPW.inp'
    write_data('result',folname,line,pathway,state,judge_spin,bond_calculation,angle_calculation,coordinate_calculation)
    print(folname)
print('This is the end of data transfer')





