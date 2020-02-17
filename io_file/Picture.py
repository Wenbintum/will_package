from ase.io import read,write
import sys,os
#The picture will be able to generate from each folder when collecting data
def gen_top(folname,filename='opt.traj')：
    """
    this function is to gennerate a series of picture with topview configuration
    Input:
    -
    Output:
    -
    """
    atoms=read(filename)
    write('{}TOP.png'.format(folname),atoms)
    os.system('mv *.png /p/project/lmcat/wenxu/data/picture')
    
