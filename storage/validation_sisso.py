#!/usr/bin/env python
import os
import numpy as np
from io_file.Write import write_data


input_content=str(raw_input("please input: ads  rung  dimension  mixID "))
root_ads= input_content.split()[0]
root_rung= int(input_content.split()[1])
root_dimension= int(input_content.split()[2])
root_mixID= int(input_content.split()[3])
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

lowest_RMSE = 100
lowest_maxAE = 100
#Example descriptor
#line_begins = [208]
#cases = [{'DD':4, 'rung':3, 'complex':10, 'opset':2, 'SIS':[300]}]

#collecting validation results
val_dict = {}
dir = '/p/project/lmcat/wenxu/jobs/SISSO' + '/r{}_{}r_{}d'.format(root_ads, root_rung, root_dimension)        
with open(dir + '/SISSO.out') as infile:
     lines = infile.readlines()
     error_begin= 0
     for line in lines:
         error_begin += 1
         if line.startswith('  {}D descriptor (model):'.format(root_dimension)):
            break
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>collecting error, descriptor, coeffient, intercept,
#Get training statistics error
err = lines[error_begin][20:]
LS_RMSE, LS_maxAE = [float(a) for a in err.split('  ')]
print 'RMSE:', LS_RMSE, 'max AE:', LS_maxAE


print "root_dimension:", root_dimension

#For collecting descriptors
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

print "desc_list:" ,desc_list 
            
#Get fitting coefficients list
coef_list=[]
coef_begin=24
if root_mixID == 0:
   coef_list=lines[error_begin + root_dimension + 2][coef_begin:].split()
   coef_list=map(float,coef_list)
   print "coef_list:",coef_list
else:
   coef_list=lines[error_begin + root_dimension + 2 + (root_mixID-1)*3][coef_begin:].split()
   coef_list=map(float,coef_list)
   print "coef_list:",coef_list

#Get intercept
if root_mixID == 0:
   intercept=float(lines[error_begin + root_dimension + 3 ][coef_begin:].strip())
   print "intercept:", intercept
else:
   intercept=float(lines[error_begin + root_dimension + 3 + (root_mixID-1)*3][coef_begin:].strip())
   print "intercept:", intercept
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>end of collecting training statics: two list, one variable

with open('validation_data') as infile:
     lines = infile.readlines()
     headers = lines[0].strip().split()
error_list=[]
for line in lines[1:]:
    values = line.strip().split()
    desc_value_list=[]
    prop = float(values[1])
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
    pred_prop = sum(map(lambda (a, b): a*b, zip(coef_list, desc_value_list))) + intercept 
    #print "desc_value_list:", desc_value_list
    print "after count:", pred_prop
    print "proper:", prop
#Calculate predicted properties
    err=pred_prop - prop
#Collect errors
    error_list.append(err)
print "error_list:", error_list
abs_error_list = [abs(x) for x in error_list]
squared_error_list = [x**2 for x in error_list]
MAE = max(abs_error_list) #max absolute error
RMSE = np.sqrt(sum(squared_error_list)/len(squared_error_list))
write_data('/p/project/lmcat/wenxu/data/SISSO','val/{}_{}r_{}d'.format(root_ads, root_rung, root_dimension), RMSE, MAE)
 

        






