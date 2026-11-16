"""Read-only: fraction of axon segments (parent->node) pointing along +x (cos>0.9), for Int->Pyr synapse-carrying segments vs all interneuron axon segments.
Segment of a synapse = node whose 'fiber piece label' equals the synapse's presynaptic axon fiber piece ID (col 8), vector node - parent. usage: xdir.py DIR..."""
import sys, glob, numpy as np, json
def run(d):
    nt={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]!='#': p=l.split(','); nt[p[1]]=p[2]
    pos={};lab={};typ={};soma={};par={}
    for ext in ('rootnodes','continuationnodes','bifurcationnodes','growthcones'):
        for l in open(glob.glob(d+'/*.'+ext)[0]):
            if l[0]=='#': continue
            p=l.split(','); i=int(p[0]); pos[i]=np.array(p[3:6],float); lab[p[1]]=i; typ[i]=p[2]; soma[i]=p[6]
            if ext!='rootnodes': par[i]=int(p[7])
    def cosx(i):
        q=par.get(i); 
        if q is None or q not in pos: return None
        v=pos[i]-pos[q]; n=np.linalg.norm(v); return v[0]/n if n>0 else None
    allc=[c for i in par if typ[i]=='axon' and nt.get(soma[i])=='interneuron' for c in [cosx(i)] if c is not None]
    sc=[];miss=0;seen=set()
    for l in open(glob.glob(d+'/*.synapses')[0]):
        if l[0]=='#': continue
        p=l.split(',')
        if p[1]!='AMPAR' and p[1]!='GABAR' and False: pass
        if nt.get(p[10])!='interneuron' or nt.get(p[11])!='pyramidal': continue
        if p[1].startswith('NMDA'): continue
        i=lab.get(p[8])
        if i is None: miss+=1; continue
        c=cosx(i)
        if c is None: miss+=1; continue
        sc.append(c)
    sc=np.array(sc); allc=np.array(allc)
    return dict(n_syn=len(sc),missing=miss,frac_x09_syn=float((sc>0.9).mean()),median_cos_syn=float(np.median(sc)),frac_x09_all=float((allc>0.9).mean()),mean_cos_all=float(allc.mean()))
if __name__=='__main__':
    for d in sys.argv[1:]: print(d.split('/')[-1],json.dumps(run(d)),flush=True)
