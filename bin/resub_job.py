#!/usr/bin/env python
import os,sys
from io_file import Write

current_dir = os.getcwd()
#copy original trajctory file
if os.path.exists('opt.traj') == True: 
   os.system('cp opt.traj copy_opt.tray')
else:
   print (" NO EXIST OPT.TRAJ FILE")
##writing reopt_str.py file
#write the module part
fname=current_dir+"/str_opt.py"
newname=current_dir+"/restr_opt.py"
Write.write_paragraph(fname,newname,"#","from","import")
#write the structure lines
with open("restr_opt.py","a" ) as outfile:
	outfile.write( "atoms=read('opt.traj')" )
	outfile.write("\n")
#write DFT setting part
Write.write_to_ending(fname,newname,"econv")

##create resub file
fname=current_dir+"/sub_job"
newname=current_dir+"/resub_job"
Write.write_final_line(fname,newname,"python restr_opt.py")
## submission
os.system("sbatch resub_job")

