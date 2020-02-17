#!/usr/bin/env python
# coding: utf-8

# In[2]:


import os,sys


# In[ ]:


###instruction:  get a series of variable into a list then write them to one line
###requirement:  pathway:  args 
def write_data(pathway,folname='folname',*args):
    args=list(args)
    #print args
    for i in range(0,len(args)):  #0 is the patheway, 1 is the folname so we start from 2
        if isinstance(args[i],float) == 'True':
           args[i]=round(args[i],4)  #keep 4 figure after point   0 is the pathway, 1 is the folname so we start from 2
        args[i]=str(args[i])
    args="  ".join(args)
    with open(pathway,'a') as output_file: ###mode 'a' means add content at the end of last line
        output_file.write(folname)
        output_file.write('  ')
        output_file.writelines(args)
        output_file.write('\n')

def write_paragraph(fname,newname,*keywords):
    file_data = ""
    data = []
    with open(fname,"r") as infile:
	for line in infile:
	   # for keyword in keywords: 
		if any(map(line.startswith,keywords)):
		    data.append(line)
		else:
		    break
		
    with open(newname,"a") as outfile:
	for line in data:
	     outfile.write(line)
def write_to_ending(fname,newname,startword):
    file_data = ""
    data = []
    startwriting = False
    with open(fname,"r") as infile:
         for line in infile:
	     if startwriting == True:
                data.append(line)
             if line.startswith(startword):
		startwriting=True
                data.append(line)
    with open(newname,"a") as outfile:
	for line in data:
	     outfile.write(line)

def write_final_line(fname,newname,finalline):
    file_data=""
    data = []
    with open(fname,"r") as infile:
             lines=infile.readlines()
             for line in lines[:-2]:
	         data.append(line)
    with open(newname,"w") as outfile:
         for line in data:
	     outfile.write(line)
         outfile.write(finalline)
	
		 
