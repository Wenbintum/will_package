#!/usr/bin/env python
import numpy as np
import random

##compute RMSE
d = [0.000, 0.166, 0.333]
p = [0.000, 0.254, 0.998]

print("d is: " + str(["%.8f" % elem for elem in d]))
print("p is: " + str(["%.8f" % elem for elem in p]))

def rmse(predictions, targets):
    return np.sqrt(((predictions - targets) ** 2).mean())

rmse_val = rmse(np.array(d), np.array(p))
print("rms error is: " + str(rmse_val))

##
