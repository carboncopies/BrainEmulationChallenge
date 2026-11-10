import sys, re
from common import *
X=sys.argv[1]; sid=int(sys.argv[2])
log=open(W+X+'/grow/run.log').read(); assert re.search(r'NES_SIM_ID=%d\b'%sid,log)
cl=client(); sim=attach(cl,sid)
if verify(sim,W+'viz_%s/sample_0000.json'%X,'grown %s sim %d'%(X,sid)):
    print(' ModelSave',sim.ModelSave('fable-r2it4-%s'%X),flush=True)
