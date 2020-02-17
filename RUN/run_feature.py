import os, sys
import numpy as np
#root
from parameter import PM
from repertory import primary_feature
from io_file   import File_oprate
from io_file.Write import write_data
###Global variable
pathway = '/p/project/lmcat/wenxu/jobs/descriptor/dos/dos_Ir'
rutile_type = 'Iro2'

#########################################################
#                        File opration                  #
#########################################################
folnames=os.listdir(pathway)
folnames.sort()
for folname in folnames: 
    list_name=['Ni','Cu','Zn','Ag','Fe','Co',
               'Ti','W', 'Mo','Mn','Ru','Ir']
    for startname in list_name:
        judge_folder=False
        if  folname.startswith('{}'.format(startname)):
            judge_folder=True
            break
    if  judge_folder == False:
        print('{} is not the working folder'.format(folname))
    else:
        print(folname)
        os.chdir('{}/{}'.format(pathway,folname))
        met,site=File_oprate.split_name(folname)

#########################################################
#           start to calclate primary feature           #
#########################################################
     #   obj_dos=primary_feature.DOS_extract(site,met,pathway='{}/{}'.format(pathway,folname))
     #   un_dbc=obj_dos.D_un_band_center()
     #   O2p_band_center=obj_dos.O2p_band_center()
     #   O2p_band_filling=obj_dos.O2p_band_filling()
     #   Max_2p_band=obj_dos.Max_2p_band()
     #   O2p_fermi=obj_dos.O2p_fermi()
     #   formation_energy=primary_feature.Formation_energy(pathway,folname,rutile_type)
     #   write_data('/p/project/lmcat/wenxu/data/feature',folname,formation_energy, O2p_band_center, O2p_band_filling, Max_2p_band, O2p_fermi, un_dbc)
     #   #gourp geometry
     #   obj_Geomerty=primary_feature.Geometry(site)
     #   obj_Geomerty.Variable()
     #   Near_1 =obj_Geomerty.Nearest_metal()[0]
     #   Near_2 =obj_Geomerty.Nearest_metal()[1]
     #   Near_3 =obj_Geomerty.Nearest_metal()[2]
     #   O_1fold =obj_Geomerty.Site_1fold()
     #   Rela_dis = obj_Geomerty.Relative_distance()
     #   Local_1=obj_Geomerty.Spherical_hamonics()[0]
     #   Local_2=obj_Geomerty.Spherical_hamonics()[1]
     #   Local_3=obj_Geomerty.Spherical_hamonics()[2]
     #   Local_4=obj_Geomerty.Spherical_hamonics()[3]
     #   Local_5=obj_Geomerty.Spherical_hamonics()[4]
     #   Local_6=obj_Geomerty.Spherical_hamonics()[5]
     #   #group dos
        obj_dos=primary_feature.DOS_extract(site,met,pathway='{}/{}'.format(pathway,folname))
        obj_dos.dos_collect()
     #   Max_d=obj_dos.Max_d_band()
     #   dbc=obj_dos.D_band_center()[0]
     #   dbw=obj_dos.D_band_width()
        dbs=obj_dos.D_band_skewness()
        write_data('/p/project/lmcat/wenxu/data/feature',folname,dbs)
     #   dbk=obj_dos.D_band_kutosis()
     #   d_band_filling=obj_dos.D_band_filling()[0]
     #   fraction_unfilling=obj_dos.D_band_filling()[1]
     #   Eg_band_center=obj_dos.Eg_band_center()[0]
     #   Eg_band_filling=obj_dos.Eg_band_filling()
     #   T2g_band_center=obj_dos.T2g_band_center()[0]
     #   T2g_band_filling=obj_dos.T2g_band_filling()
     #   Dos_fermi=obj_dos.Dos_fermi()
     #   O2p_band_center=obj_dos.O2p_band_center()
     #   O2p_band_filling=obj_dos.O2p_band_filling()
     #   
     #   
     #   Ef = primary_feature.Fermi_level(pathway,folname)
     #   WF = primary_feature.Work_function(site,Ef,pathway='{}/{}'.format(pathway,folname))
     #   PE = primary_feature.Atomic_feature(met,site,rutile_type)[0]
     #   IE = primary_feature.Atomic_feature(met,site,rutile_type)[1]
     #   EA = primary_feature.Atomic_feature(met,site,rutile_type)[2]
     #   radius= primary_feature.Atomic_feature(met,site,rutile_type)[3]
     #   Vad2= primary_feature.Atomic_feature(met,site,rutile_type)[4]
     #   bader_charge = primary_feature.Bader_charge(met,site,rutile_type)[0]
     #   aver_metal = primary_feature.Bader_charge(met,site,rutile_type)[1]
     #   aver_Oxygen = primary_feature.Bader_charge(met,site,rutile_type)[2]
     #   
     #  # print 'Nearest_metal', Nearest_M
     #  # print 'Site_1fold', O_1fold
     #  # print 'Relative_distance', Relative_dis
     #  # print 'Local_order_parameter', Local_order
     #  # print 'Work_function', WF
     #  # print 'Atomic feature', Atomic_feature
     #  # print 'Max_d_band', Max_d
     #  # print 'D_band_center', dbc
     #  # print 'D_band_width', dbw
     #  # print 'D_band_skewness', dbs
     #  # print 'D_band_kutosis', dbk
     #  # print 'D_band_filling', d_band_filling
     #  # print 'fraction_unfilling', fraction_unfilling
     #  # print 'Eg_band_center',Eg_band_center
     #  # print 'Eg_band_filling', Eg_band_filling
     #  # print 'T2g_band_center', T2g_band_center
     #  # print 'T2g_band_filling', T2g_band_filling
     #  # print 'Dos_fermi', Dos_fermi
     #  # print 'O2p_band_center', O2p_band_center
     #  # print 'O2p_band_filling', O2p_band_filling
     #  # print 'bader_charge', bader_charge
     #  # print 'bader_aver_metal',aver_metal
     #  # print 'bader_aver_Oxygen',aver_Oxygen
     #   write_data('/p/project/lmcat/wenxu/data/feature',folname, O_1fold, Rela_dis, Near_1, Near_2, Near_3, Local_1, Local_2, Local_3, Local_4, Local_5, Local_6,
     #                                                             Max_d, dbc, dbw, dbk, d_band_filling, fraction_unfilling, Eg_band_center, Eg_band_filling, T2g_band_center,
     #                                                             T2g_band_filling, Dos_fermi, O2p_band_center, O2p_band_filling, WF, PE, IE, EA, radius, Vad2,
     #                                                             bader_charge, aver_metal, aver_Oxygen)
    os.chdir(pathway)

