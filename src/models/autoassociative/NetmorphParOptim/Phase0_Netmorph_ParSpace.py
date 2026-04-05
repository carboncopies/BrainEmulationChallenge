import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import openpyxl
from scipy import stats
from scipy.stats import qmc   # for Latin Hypercube
import warnings
warnings.filterwarnings('ignore')
import os


path='/home/mgabr001/BrainGenix/BrainEmulationChallenge/src/models/autoassociative/NetmorphParOptim'

os.chdir(path)

# Parameters under investigation (Min-Max, # of bins): TOTAL par space = 6 * 15 * 15 * 6 * 11 * 4 * 10 = 3,564,000
# days                20 - 25    # 6
# pyramidal           16 - 128   # 15
# interneuron         16 - 128   # 15
# minneuronseparation 10 - 15    # 6
# shape.radius        100 - 200  # 11
# shape.thickness     20 - 50    # 4
# dm.weight           0.1 - 1.0  # 10

l_bounds = np.array([20, 16, 16, 10, 100, 20, 0.1 ])
# Upper bounds are selected 1 increment higher than the required range, since the lower bound of the bin (lb, lb+inc) is being assigned 
# (for example, all values between (25, 26) are assigned 25 which is the required max value for days)   
u_bounds = np.array([26, 136, 136, 16, 210, 60, 1.1]) 
increments = np.array([1, 8, 8, 1, 10, 10, 0.1 ])

sampler = qmc.LatinHypercube(d=7, rng = 2727)   # fix random number generator seed for reproducability 
sample = sampler.random(n=700) 

scaled_smp = qmc.scale(sample, l_bounds, u_bounds)

# qmc.discrepancy(sample)
print(scaled_smp[:5,:])

for j in range(scaled_smp.shape[1]):
    lb = l_bounds[j]
    ub = l_bounds[j]+increments[j]
    inc = increments[j]

    bins = (u_bounds - l_bounds) / increments
    
    for k in range( int(bins[j]) ):
        for i in range(scaled_smp.shape[0]):
            if scaled_smp[i,j] > lb and scaled_smp[i,j] < ub:
                scaled_smp[i,j] = lb
        lb = ub
        ub = lb + inc

print(scaled_smp[:5,:])

print(scaled_smp.shape)


# Create Dataframe based from scaled_smp data.

cols = ['days','pyramidal','interneuron','minneuronseparation','shape.radius','shape.thickness','dm.weight ']
df = pd.DataFrame(data = scaled_smp, columns = cols)

df = df.astype({'days':'int'})
df = df.astype({'pyramidal':'int'})
df = df.astype({'interneuron':'int'})
df = df.astype({'minneuronseparation':'int'})
df = df.astype({'shape.radius':'int'})
df = df.astype({'shape.thickness':'int'})
df = df.astype({'dm.weight ':'float'})

# Drop Index inplace
df.reset_index(drop=True, inplace=True)
# write 700 samples into the excel file.
with pd.ExcelWriter("ParameterSpace_set1_700_samples.xlsx") as writer:
    df.iloc[:700].to_excel(writer, index=False)  
   
print(df.shape)
print(df.head(10))


