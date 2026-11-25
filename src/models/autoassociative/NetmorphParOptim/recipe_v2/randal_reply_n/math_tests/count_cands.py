import mtlib as M, numpy as np, time
for s in M.SEEDS:
    t=time.time(); P=M.G(s); c=M.O.candidates(P,2)
    print(s,len(c),sum(len(x[1]) for x in c),round(time.time()-t,1),flush=True)
