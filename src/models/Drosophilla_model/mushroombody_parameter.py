import pandas as pd
import numpy as np
import openpyxl
from scipy import stats
from scipy.stats import qmc   # for Latin Hypercube
import warnings
warnings.filterwarnings('ignore')
import os


path='/home/tifftma/BrainGenix/BrainEmulationChallenge/src/models/Drosophilla_model'

os.chdir(path)

# Parameters under investigation (Min-Max, # of bins): TOTAL par space = 5*13*9*5*10*15 = 439,875
# Parameters under investigation (Min-Max, # of bins):
#   days                  19 - 23   5
#   KC.shape.radius       200 - 800 13
#   KC.shape.thickness    100 - 500 9
#   KC.minneuronseparation 10 - 30  5
#   dm.weight             0.1 - 1.0 10   
#   KC.pyramidal          16 - 128  15     
l_bounds = np.array([19,  200, 100, 10, 0.1, 16 ])
u_bounds = np.array([24,  850, 550, 35, 1.1, 136])
increments = np.array([1, 50,  50,  5,  0.1, 8  ])
 
cols = ['days', 'KC.shape.radius', 'KC.shape.thickness',
        'KC.minneuronseparation', 'dm.weight', 'KC.pyramidal']
 
N_SAMPLES = 700  
 
sampler = qmc.LatinHypercube(d=len(cols), rng=2727) 
sample = sampler.random(n=N_SAMPLES)
 
scaled_smp = qmc.scale(sample, l_bounds, u_bounds)
 
print("First 5 raw LHS samples (continuous, pre-discretization):")
print(scaled_smp[:5, :])

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


# Create Dataframe based from scaled_smp data.
int_cols = ['days', 'KC.shape.radius', 'KC.shape.thickness',
            'KC.minneuronseparation', 'KC.pyramidal']
df = pd.DataFrame(data = scaled_smp, columns = cols)
for c in int_cols:
    df = df.astype({c: 'int'})
df = df.astype({'dm.weight': 'float'})

# Drop Index inplace
df.reset_index(drop=True, inplace=True)
 
print(f"\nFinal sample sheet shape: {df.shape}")
print(df.head(20))
 
with pd.ExcelWriter('MushroomBody_ParSpace_700_samples.xlsx') as writer:
    df.to_excel(writer, index=False)
 
print("\nSaved to MushroomBody_ParSpace_700_samples.xlsx")