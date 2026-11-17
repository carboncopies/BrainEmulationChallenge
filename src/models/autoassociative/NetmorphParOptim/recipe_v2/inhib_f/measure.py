"""Per-cell arbor length/extent from NetMorph txt output. Length = sum over nodes of Euclidean distance to parent node (um, NetMorph coords).
Nodes from rootnodes (no parent col; roots have parent=none), continuationnodes, bifurcationnodes, growthcones. Parent index = 'node index number'."""
import glob, collections, numpy as np, sys
def load(d):
    nt={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]!='#': p=l.split(','); nt[p[1]]=(p[2],np.array(p[4:7],float))
    pos={}; par={}; typ={}; soma={}
    for ext in ('rootnodes','continuationnodes','bifurcationnodes','growthcones'):
        for l in open(glob.glob(d+'/*.'+ext)[0]):
            if l[0]=='#': continue
            p=l.split(','); i=int(p[0]); pos[i]=np.array(p[3:6],float); typ[i]=p[2]; soma[i]=p[6]
            if ext!='rootnodes': par[i]=int(p[7])
    return nt,pos,par,typ,soma
def measure(d):
    nt,pos,par,typ,soma=load(d)
    L=collections.defaultdict(float); ext=collections.defaultdict(list); n=collections.Counter(); miss=0
    ids=np.array(list(pos)); 
    for i,pi in par.items():
        if pi not in pos: miss+=1; continue
        k=(soma[i],typ[i]); L[k]+=float(np.linalg.norm(pos[i]-pos[pi])); n[k]+=1
        ext[k].append(np.linalg.norm(pos[i]-nt[soma[i]][1]))
    # root segment: root->soma not counted
    out={}
    for (s,t),v in L.items():
        out.setdefault(nt[s][0],{}).setdefault(t,[]).append((s,v,max(ext[(s,t)]),float(np.percentile(ext[(s,t)],90)),n[(s,t)]))
    return out,miss
def summarize(d):
    out,miss=measure(d); res={'missing_parent':miss}
    for ct in out:
        for t,rows in out[ct].items():
            a=np.array([[r[1],r[2],r[3],r[4]] for r in rows])
            res['%s_%s'%(ct,t)]=dict(n=len(a),len_mean=a[:,0].mean(),len_median=float(np.median(a[:,0])),len_min=a[:,0].min(),len_max=a[:,0].max(),maxreach_mean=a[:,1].mean(),maxreach_max=a[:,1].max(),p90reach_mean=a[:,2].mean(),nodes_mean=a[:,3].mean())
    return res
if __name__=='__main__':
    import json; r=summarize(sys.argv[1]); print(json.dumps(r,indent=1,default=float))
