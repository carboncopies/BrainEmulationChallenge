import sys, json, itertools
import numpy as np
P='/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim'
sys.path.insert(0, P+'/weight_space')
from reservoir import Reservoir
S=sys.argv[1]
D='/home/johnjose/cos/netmorph_work/fable_loop/r2_seeds/'
r=Reservoir(D+'viz_%s/sample_0000.json'%S)
G=r.G[1]; GA=r.G[2]
pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
A=G
def f(x): return '['+', '.join('%.2f'%v for v in x)+']'
def search(avail):
    avail=np.array(sorted(avail)); n=len(avail)
    best=None
    combos=itertools.combinations(range(n),4)
    while True:
        chunk=list(itertools.islice(combos,50000))
        if not chunk: break
        idx=np.array(chunk)            # local indices
        gid=avail[idx]                 # (K,4) global ids
        V=A[gid][:,:,avail].min(axis=1)  # (K,n)
        rows=np.arange(len(idx))[:,None]
        V[rows,idx]=-np.inf
        top=-np.sort(-V,axis=1)[:,:4]
        score=top[:,3]; ssum=top.sum(axis=1)
        order=np.lexsort((-ssum,-score)); b=order[0]
        cand=(score[b],ssum[b],gid[b].copy(),V[b].copy())
        if best is None or (cand[0],cand[1])>(best[0],best[1]): best=cand
    sc,ss,C,v=best
    nc=[int(avail[j]) for j in np.argsort(-v,kind='stable')[:4]]
    return sorted(int(c) for c in C), sorted(nc), float(sc)
avail=set(pyr); groups=[]
for g in range(3):
    C,NC,sc=search(avail)
    groups.append((C,NC,sc)); avail-=set(C)|set(NC)
members=lambda g: sorted(g[0]+g[1])
for k,(C,NC,sc) in enumerate(groups):
    print('GROUP %d: members %s cue %s noncue %s'%(k,members(groups[k]),C,NC))
    mn=min(A[c,m] for c in C for m in NC)
    print('  search score %.4f ; min cue->noncue pair nS %.4f'%(sc,mn))
    print('  ASSERT score>=4.5: %s'%('PASS' if mn>=4.5 else 'FAIL'))
grouped=set(m for g in groups for m in members(g))
cueset={c:k for k,g in enumerate(groups) for c in g[0]}
wpost={}
for k,(C,NC,sc) in enumerate(groups):
    print('--- GROUP %d detail'%k)
    print(' a. non-cue: id w_post S_post ; recurrent drive from other 3 noncue under ENG ; ')
    for m in NC:
        Sp=sum(float(A[c,m]) for c in C); w=1.0 if Sp==0 else min(1.0,27.44/Sp); wpost[m]=w
    for m in NC:
        rec=sum(wpost[m]*float(A[o,m]) for o in NC if o!=m)
        print('   %d: w_post=%.4f S_post=%.2f recurrent_drive_ENG=%.2f'%(m,wpost[m],sum(float(A[c,m]) for c in C),rec))
    for c in C:
        print('   cue %d: drive from 4 noncue at w=1 = %.2f'%(c,sum(float(A[o,c]) for o in NC)))
    print(' b. cue->cue pair sums (other 3 cue, w=1): '+', '.join('%d:%.2f'%(c,sum(float(A[o,c]) for o in C if o!=c)) for c in C)+' ; max %.2f'%max(sum(float(A[o,c]) for o in C if o!=c) for c in C))
G0=groups
def Cgi(k,i): return sum(float(G[c,i]) for c in G0[k][0])
def inhw(p,i):
    if p in cueset:
        C=Cgi(cueset[p],i); assert C>0
        return min(1.0,10.0/C)
    return 1.0
intlist={}
for k,g in enumerate(G0):
    mem=members(g); C=g[0]; rows=[]; ids=[]
    for i in its:
        d8=sum(float(G[m,i]) for m in mem)
        if d8>=14:
            c1=sum(float(G[c,i]) for c in C)
            ci=sum(float(G[c,i])*inhw(c,i) for c in C if G[c,i]>0)
            fi=sum(float(G[m,i])*inhw(m,i) for m in mem if G[m,i]>0)
            rows.append('%d: %.2f / %.2f / %.2f / %.2f'%(i,c1,d8,ci,fi)); ids.append(i)
    intlist[k]=ids
    print('--- GROUP %d c. interneurons (cue-only w1 / all8 w1 / cue-only INHfb / all8 INHfb): %s'%(k,'; '.join(rows) if rows else 'none'))
    print(' d. GABA per member (total from all int / from listed int):')
    for m in mem:
        print('   %d: total %.2f ; listed %.2f'%(m,sum(float(GA[i,m]) for i in its),sum(float(GA[i,m]) for i in ids)))
print('=== e. spread table (w=1)')
for a in range(3):
    ma=members(groups[a]); nca=groups[a][1]
    for b in range(3):
        if a==b: continue
        mb=members(groups[b])
        s8=[sum(float(A[m,t]) for m in ma) for t in mb]
        snc=[sum(float(A[m,t]) for m in nca) for t in mb]
        print(' G%d->G%d targets %s'%(a,b,mb))
        print('   S8  %s max %.2f'%(f(s8),max(s8)))
        print('   SNC %s max %.2f'%(f(snc),max(snc)))
    ung=[p for p in pyr if p not in grouped]
    s8=np.array([sum(float(A[m,t]) for m in ma) for t in ung]); sn=[sum(float(A[m,t]) for m in nca) for t in ung]
    o=np.argsort(-s8,kind='stable')[:8]
    print(' G%d -> ungrouped pyr (%d cells) top8 S8/SNC: %s'%(a,len(ung),'; '.join('%d:%.2f/%.2f'%(ung[j],s8[j],sn[j]) for j in o)))
    print('   count ungrouped S8>=80: %d, >=140: %d, >=200: %d'%((s8>=80).sum(),(s8>=140).sum(),(s8>=200).sum()))
json.dump({'groups':[{'members':members(g),'cue':g[0],'noncue':g[1],'score':g[2]} for g in groups],'w_post':{str(k):v for k,v in wpost.items()},'interneurons':{str(k):v for k,v in intlist.items()}},open(D+'design_%s.json'%S,'w'))
