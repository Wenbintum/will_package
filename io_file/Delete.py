#!/usr/bin/env python
# coding: utf-8

# In[1]:


#instruction: In order to delete the wave function file in esp.log release space
import os,sys


# In[2]:


def del_qe():
    pathway=os.getcwd()
    folnames=os.listdir(pathway)
    folnames.sort()
    for folname in folnames:
        os.chdir(folname)
        if os.path.exits('esp.log'):
            os.chdir('esp.log')
            os.system('rm -r qe*')    ###delete qexxxxx folder 
        else:
            print('esp.log does not exist, delete calc.save')
            os.system('rm -r calc.save')
        continue
    print('This is the end of clean space')


# In[ ]:




