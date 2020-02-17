from ase.io import read,write
import sys,os
#root
from io_file.Picture import gen_top
pathway=""
folnames = os.listdir(pathway)
folnames.sort()
for folname in folnames:
    os.chdir('{}/{}'.fotmat(pathway,folname))
    gen_top(folname,filename='opt.traj')
    os.chdir(pathway)

    