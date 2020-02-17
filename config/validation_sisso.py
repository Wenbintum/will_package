#!/usr/bin/env python
import os
import numpy as np
from io_file.Write import write_data
import configparser
import codecs
#configparser
config=configparser.ConfigParser()
config.read('config_validation')
#config.readfp(codecs.open('config_validation','r','ascii'))

pathway=config.get('root','pathway')
val_name=config.get('root','val_name')
root_name=config.get('root','root_name')
#root_rung=config.getint('root','number_rung')
root_rungs= [0,1,2]
root_dimensions=[1,2,3,4,5,6,7,8]
opt_dimension=config.getint('root','opt_dimension')
#root_dimension= 3 

type_ads=config.get('root','type_ads')
length_ads=config.get('root','length_ads')
N_ads=len(type_ads.split())



#transfer the operator to the form that can be recognized in python
replacement_dict = {'exp':'np.exp', 'exp-(':'np.exp(-', '^':'**', 'sqrt':'np.sqrt', 'log':'np.log', 'sin':'np.sin', 'cos':'np.cos'}
def cbrt(x):
    if x>0:
        return x**(1./3.)
    elif x<0:
        return -abs(x)**(1./3.)
    elif x==0:
        return 0
def scd(x):
    return 1./(np.pi*(1+x**2))

for root_rung in root_rungs:
        #opt_name_error
        opt_name_error={}
	for root_dimension in root_dimensions:
		#in terms of root_ads root_rung root_dimension to find error begin
		dir = eval(pathway) + '/{}_{}r_{}d'.format(root_name, root_rung, root_dimension)
		with open(dir+'/SISSO.out'.format(dir),'r') as infile:
		     lines = infile.readlines()
		     error_begin= 0
		     for line in lines:
			 error_begin += 1
			 if line.startswith('  {}D descriptor (model):'.format(root_dimension)):
			    break
		#Get training statistics error
		err = lines[error_begin][20:]
		LS_RMSE, LS_maxAE = [float(a) for a in err.split('  ')]
		print 'RMSE:', LS_RMSE, 'max AE:', LS_maxAE
		###looking for the descriptor from SISSO.out for all ads once
		desc_begin=24
		desc_list = []
		D1 = lines[error_begin + 2][desc_begin:]
		D1 = D1[1:-2]
		desc_list.append(D1)
		if root_dimension > 1:
		    D2 = lines[error_begin + 3][desc_begin:]
		    D2 = D2[1:-2]
		    desc_list.append(D2)
		    #print D2
		    if root_dimension > 2:
			D3 = lines[error_begin + 4][desc_begin:]
			D3 = D3[1:-2]
			#print D3
			desc_list.append(D3)
			if root_dimension > 3:
			    D4 = lines[error_begin + 5][desc_begin:]
			    D4 = D4[1:-2]
			    desc_list.append(D4)
			    #print D4
			    if root_dimension > 4:
				D5 = lines[error_begin + 6][desc_begin:]
				D5 = D5[1:-2]
				desc_list.append(D5)
				#print D5
				if root_dimension > 5:
				    D6 = lines[error_begin + 7][desc_begin:]
				    D6 = D6[1:-2]
				    desc_list.append(D6)
				    #print D6
				    if root_dimension > 6:
				       D7 = lines[error_begin + 8][desc_begin:]
				       D7 = D7[1:-2]
				       desc_list.append(D7)
				       #print D7
				       if root_dimension > 7:
					   D8 = lines[error_begin + 9][desc_begin:]
					   D8 = D8[1:-2]
					   desc_list.append(D8)
					   #print D8
		print "desc_list", desc_list
		#Get fitting coefficients for different phase (O,OH,OOH) loop
		#define a dictionary to store the ads and respective coef_list
		coef_dic={}
		coef_list=[]
		coef_begin=24
		intercept_dic={}
		for i in range(N_ads):
		       coef_list=lines[error_begin + root_dimension + 2 + i*3][coef_begin:].split()
		       coef_list=map(float,coef_list)
		       coef_dic[type_ads.split()[i]]=coef_list
		       intercept=float(lines[error_begin + root_dimension + 3 + i*3][coef_begin:].strip())
		       intercept_dic[type_ads.split()[i]]=intercept
		print "coef_dic:", coef_dic
		print "intercept_dic:", intercept_dic
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>end of collecting training statics: two list, one variable

		with open(val_name,'r') as infile:
		     lines = infile.readlines()
		     headers = lines[0].strip().split()
		error_list=[]
		number_line=0
		#>>>>>>>>>>>>>>>>>>>>name error list
		name_error_list=[]
		for line in lines[1:]:
		    #count the line that have been operated
		    number_line = number_line + 1 

		    values = line.strip().split()
		    desc_value_list=[]
		    prop = float(values[1])
		    name_error_list.append(values[0])
		    #Replace primary feature names by their values, mathematical operator names by numpy functions, and evaluate descriptors
		    for desc0 in desc_list:
			for i,header in enumerate(headers):
			    header_value = values[i]
			    desc0=desc0.replace(header,header_value)
			for pattern in replacement_dict:
			    if pattern in desc0:
			       desc0 = desc0.replace(pattern, replacement_dict[pattern])
			       #print desc0
			desc0 = eval(desc0)
			desc_value_list.append(desc0) 
		#Calculate predicted properties
		    desc_value_list=map(float,desc_value_list)
		    ### judge wich ads calculated now and give index
		    for j, length_line in enumerate(length_ads.split()):
			length_line = int(length_line)
			if number_line < length_line:
			   pred_prop = sum(map(lambda (a, b): a*b, zip(coef_dic[type_ads.split()[j]], desc_value_list))) + intercept_dic[type_ads.split()[j]]
			   break
		    #print "desc_value_list:", desc_value_list
		    #print "after count:", pred_prop
		    #print "proper:", prop
		#Calculate predicted properties
		    err=pred_prop - prop
		#Collect errors
		    error_list.append(err)
		print "length error", len(error_list), "error_list:", error_list
	#################only count OH and OOH, firstly we get whole erorr_list then we get a part of it based on which ads we want to cal
	#####this can be modified to calculate each ads by the length of samples
		#error_list=error_list[int(length_ads.split()[0])-1 : int(length_ads.split()[1])-1]   # only from OH        
		#error_list=error_list[int(length_ads.split()[0])-1 : ]     #from OH to OOH
		error_list=error_list[ : ]     #for O OH OOH
		print "length OH error", len(error_list), "error_list:", error_list
		abs_error_list = [abs(x) for x in error_list]
		squared_error_list = [x**2 for x in error_list]
		MAE = max(abs_error_list) #max absolute error
		id_line= abs_error_list.index(max(abs_error_list))
		print "max error line", id_line + 2
		RMSE = np.sqrt(sum(squared_error_list)/len(squared_error_list))
	#>>>>>>>>>>>>>>>export the name of top error line and correspending error. convert  abs_error_list[] and name_error_list to dic.
	        #this is the name_error_list starting from OH
        	#name_error_list=name_error_list[int(length_ads.split()[0])-1 : ] 
        	name_error_list=name_error_list[ : ] 
		dic_name_error = dict(zip(name_error_list,abs_error_list))
		print sorted(dic_name_error.items(),key=lambda item:item[1],reverse=True)
		if root_dimension == opt_dimension:   #export from the final time
		   opt_name_error=sorted(dic_name_error.items(),key=lambda item:item[1],reverse=True)
        	name_error_list=name_error_list[int(length_ads.split()[0])-1 : ] 

		write_data('/p/project/lmcat/wenxu/data/SISSO','val/{}_{}r_{}d'.format(root_name, root_rung, root_dimension), RMSE, MAE)
	#print "1111111", str(opt_name_error)
	if  opt_name_error:
	    for i in range(len(opt_name_error)):
		line_name_error=str(opt_name_error[i])
		write_data('/p/project/lmcat/wenxu/data/SISSO', line_name_error)
	else:
	    exit





