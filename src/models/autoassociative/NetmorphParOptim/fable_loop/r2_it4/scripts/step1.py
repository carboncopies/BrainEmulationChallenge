import sys
from common import *
X=sys.argv[1]
cl=client()
c=NES.Simulation.Configuration(); c.Name='fable-r2it4-%s-copy'%X; c.Seed=0
C=cl.CreateSimulation(c); print('NEW SIM ID',C.ID,flush=True)
open(W+X+'/C_id.txt','w').write(str(C.ID))
C.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
C.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
C.SetSTDP(_DoSTDP=False)
r=C.ModelLoad('fable-r2it4-%s'%X); print('ModelLoad',r,flush=True)
print('verify C', verify(C,W+'viz_%s/sample_0000.json'%X,'copy %d'%C.ID))
