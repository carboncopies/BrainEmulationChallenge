import sys, numpy as np
W='/home/johnjose/cos/netmorph_work'
P=W+'/bec/src/models/autoassociative/NetmorphParOptim'
sys.path.insert(0,P+'/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/it1/viz_a/sample_0000.json')
A,Gb,Nm=r.G[1],r.G[2],r.G[3]
groups=[[4,18,20,22,29,51,59,63],[8,27,33,39,41,42,44,60],[0,12,17,19,21,37,49,50],[15,16,31,35,36,43,48,64]]
cues=[[22,29,51,63],[8,27,33,44],[12,17,19,50],[16,36,43,64]]
pyr=list(map(int,r.pyr)); ints=list(map(int,r.int))
for g in groups:
    for m in g: assert m in pyr, m
def f(x): return '[' + ', '.join('%.1f'%v for v in x) + ']'
def rng(l):
    if l==list(range(l[0],l[-1]+1)): return '%d..%d (contiguous, n=%d)'%(l[0],l[-1],len(l))
    return str(l)
allg=set(sum(groups,[]))
nong=[p for p in pyr if p not in allg]
print('A. pyr:',rng(pyr)); print('   int:',rng(ints))
print('\nB. within-group')
for gi,(g,c) in enumerate(zip(groups,cues)):
    nc=[m for m in g if m not in c]
    print('G%d members %s cue %s'%(gi,g,c))
    print(' (1) AMPA from 4 cues to non-cue',nc,f([A[c,m].sum() for m in nc]))
    print(' (2) AMPA from other 7 per member',f([A[[x for x in g if x!=m],m].sum() for m in g]))
    print(' (3) 8x8 AMPA submatrix (rows pre, cols post):')
    for a in g: print('    pre %2d'%a,f([A[a,b] for b in g]))
    print(' (4) NMDA from other 7 per member',f([Nm[[x for x in g if x!=m],m].sum() for m in g]))
print('\nC. cross-talk')
for a in range(4):
    for b in range(4):
        if a==b: continue
        print('G%d->G%d'%(a,b))
        for m in groups[b]:
            v=A[groups[a],m]; print('   post %2d'%m,f(v),'max %.1f'%v.max())
print('\nD. background (non-member pyr n=%d)'%len(nong))
for gi in range(4):
    for lab,src in (('8 members',groups[gi]),('4 cues',cues[gi])):
        v=A[np.ix_(src,nong)].sum(0)
        print('G%d %s: >=13.84: %d, >=27.44: %d, max %.1f'%(gi,lab,(v>=13.84).sum(),(v>=27.44).sum(),v.max()))
print('\nE. interneuron table')
print('id | AMPA_in_total | AMPA from G0-3 members | from G0-3 cues | n_pre_pyr | GABA_out_to_pyr_total | GABA onto G0-3 members | GABA_in_from_int | GABA_out_to_int')
for i in ints:
    print(i,'|%.1f'%A[pyr,i].sum(),'|',f([A[g,i].sum() for g in groups]),'|',f([A[c,i].sum() for c in cues]),'|',int((A[pyr,i]>0).sum()),
      '|%.1f'%Gb[i,pyr].sum(),'|',f([Gb[i,g].sum() for g in groups]),'|%.1f'%Gb[ints,i].sum(),'|%.1f'%Gb[i,ints].sum())
print('\nF. interneuron sets')
for gi,g in enumerate(groups):
    S=[i for i in ints if A[g,i].sum()>=13.84]
    print('G%d S:'%gi,', '.join('%d:%.1f'%(i,A[g,i].sum()) for i in S))
    for hi,h in enumerate(groups):
        print('   GABA from S onto G%d members'%hi,f(Gb[np.ix_(S,h)].sum(0)) if S else '[]')
    if S:
        v=Gb[np.ix_(S,nong)].sum(0)
        print('   non-member pyr: mean %.1f, >=8: %d, >=40: %d (n=%d)'%(v.mean(),(v>=8).sum(),(v>=40).sum(),len(nong)))
print('\nG. total GABA from all interneurons per member')
for gi,g in enumerate(groups): print('G%d'%gi,f(Gb[np.ix_(ints,g)].sum(0)))
print('\nH. top-8 presynaptic pyr for interneurons with AMPA in >=13.84')
for i in ints:
    if A[pyr,i].sum()>=13.84:
        col=A[pyr,i]; o=np.argsort(-col)[:8]
        print(i,', '.join('%d:%.1f'%(pyr[k],col[k]) for k in o))
print('\nI. Pyr->Int AMPA pairs: %d ; sum NMDA pyr->int: %.3f'%(int((A[np.ix_(pyr,ints)]>0).sum()),Nm[np.ix_(pyr,ints)].sum()))
