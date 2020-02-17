import numpy as np
from sklearn.model_selection import StratifiedKFold,KFold
a=np.loadtxt('overall.dat',dtype=('|S25'))
#y=[1]*194 + [2]*195 + [3]*191
y=[1]*189 + [2]*185
sfolder = StratifiedKFold(n_splits=5,shuffle=True)
train_list=[]; test_list=[]
for train, test in sfolder.split(a,y):
    train_list.append(train)
    test_list.append(test)
for index, i in enumerate(range(1,6)):
    np.savetxt("train{}.py".format(i),a[train_list[index]],fmt="%s") 
    np.savetxt("test{}.py".format(i),a[test_list[index]],fmt="%s")

