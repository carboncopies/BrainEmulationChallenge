"""Offline per-cell morphology of E4 networks (V1 arbor, 20 interneurons, line-379-fixed) from NetMorph txt output. No sims.
Per cell and fibre class (axon / dendrite): total length (sum of node-to-parent distances; root->soma stub not counted), branch points
(bifurcationnodes), tips (growthcones), max and p90 Euclidean distance from soma, max path... Reuses the loader logic of linefix/measure.py."""
import glob, json, sys, collections, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/linefix')
ROOTS=['/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/','/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/']
def finddir(u):
    for r in ROOTS:
        g=glob.glob(r+u+'/*_net.txt.neurons')
        if g: return r+u
def load(d):
    nt={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]!='#': p=l.split(','); nt[p[1]]=(p[2],np.array(p[4:7],float))
    pos={};par={};typ={};soma={};kind={}
    for ext in ('rootnodes','continuationnodes','bifurcationnodes','growthcones'):
        for l in open(glob.glob(d+'/*.'+ext)[0]):
            if l[0]=='#': continue
            p=l.split(','); i=int(p[0]); pos[i]=np.array(p[3:6],float); typ[i]=p[2]; soma[i]=p[6]; kind[i]=ext
            if ext!='rootnodes': par[i]=int(p[7])
    return nt,pos,par,typ,soma,kind
def measure(d):
    nt,pos,par,typ,soma,kind=load(d)
    S=collections.defaultdict(lambda: dict(L=0.0,br=0,tips=0,dist=[]))
    for i,pi in par.items():
        if pi not in pos: continue
        k=(soma[i],typ[i]); s=S[k]; s['L']+=float(np.linalg.norm(pos[i]-pos[pi]))
        s['dist'].append(float(np.linalg.norm(pos[i]-nt[soma[i]][1])))
        if kind[i]=='bifurcationnodes': s['br']+=1
        if kind[i]=='growthcones': s['tips']+=1
    res=collections.defaultdict(list)
    for (sm,t),s in S.items():
        res[(nt[sm][0],t)].append([s['L'],s['br'],s['tips'],max(s['dist']),float(np.percentile(s['dist'],90))])
    return res
if __name__=='__main__':
    models=json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/models.json'))
    allres={}
    for k,u in models.items():
        d=finddir(u)
        if not d: print('MISSING',k,u); continue
        r=measure(d); allres[k]={'%s|%s'%kk:np.array(v).mean(0).tolist()+[len(v)] for kk,v in r.items()}
    json.dump(allres,open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/morph_e4.json','w'),indent=1)
    keys=sorted({c for m in allres.values() for c in m})
    for c in keys:
        a=np.array([m[c] for m in allres.values() if c in m])
        print(c,'n_models',len(a),'| mean over models of per-cell means: len %.0f (SD %.0f) branch pts %.0f tips %.0f maxdist %.0f p90dist %.0f'%(a[:,0].mean(),a[:,0].std(ddof=1),a[:,1].mean(),a[:,2].mean(),a[:,3].mean(),a[:,4].mean()))
