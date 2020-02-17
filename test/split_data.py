#!/usr/bin/env python
import numpy as np
import random
#read feature file 
with open('OOH.dat','r') as input_file:
     data=input_file.readlines()
data1=data[1:]
random.shuffle(data1)
number_column=len(data1[0].split())
number_training=int(round(len(data1)*0.5))
number_validation=int(round(len(data1)*0.25))
number_test=len(data1) - number_training - number_validation
feature_data=[[0 for x in range(number_column)] for y in range(len(data1))]
for i in range(len(data1)):
    for j in range(number_column):
        feature_data[i][j]=data1[i].split()[j]
#with open('training_data','w') as output_file:
#     output_file.write(str(feature_data))
    # for i in range(number_training):
    #     for j in range(number_column):
    #         output_file.write(feature[i][j])
with open('training_data','w') as output_file:
	write_data=""
        write_data += data[0]
	for line in data1[:number_training]:
    		write_data += line
        output_file.write(write_data)
with open('validation_data','w') as output_file:
        validation_data=""
        validation_data += data[0]
        for line in data1[number_training:number_training + number_validation]:
                validation_data += line
        output_file.write(validation_data)
with open('test_data','w') as output_file:
        test_data=""
        test_data += data[0]
        for line in data1[number_training + number_validation:]:
                test_data += line
        output_file.write(test_data)






 
