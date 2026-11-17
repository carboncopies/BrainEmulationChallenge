import json
a=json.load(open('pv_results.json')); b=json.load(open('../inhib_e/pv_results.json'))
import sys; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); import recipelib as L
def stat(tag,src,dirn):
    v=src[tag]; D=L.Dump(dirn+'/grow_%s/viz/sample_0000.json'%tag); nz=int((D.G[:96,:96]>0).sum())
    return dict(p=nz/9120,spc=v['pyr_pyr']/nz,A=100*v['inhib_frac_ip_over_ip_pp'],IP=v['int_pyr']/v['pairs_int_pyr'],PI=v['pyr_int']/v['pairs_pyr_int'],drv=v['drivable_8cell_capaware'],n=v['n_int'],zero=v['zero_pyr_input'],PP=v['pyr_pyr'])
CFG={'E4':('V1n20','0.03'),'E5':('V3n24','0.02'),'E6':('V3n20','0.02')}
R={}
for e,(n,d) in CFG.items():
    for s in (16180,27182,31415):
        tag='%s_s%d_p0d0175_i0d%s'%(n,s,d[2:]); 
        R[(e,s)]=stat(tag,b,'../inhib_e') if s==16180 else stat(tag,a,'.')
def bars(r):
    third=r['n']/3.0
    return {1:0.1<=r['p']<=0.3,2:1.9<=r['spc']<=4.5,3:4<=r['IP']<=9,4:1.5<=r['PI']<=4.5,5:r['drv']>=(7 if r['n']==20 else 8),6:True,7:25<=r['A']<=50}
P={('E4',27182):dict(p=.227,spc=1.95,A=42.3,IP=3.59,PI=4.67,drv=11),('E4',31415):dict(p=.290,spc=1.85,A=44.1,IP=3.77,PI=4.38,drv=10),
('E5',27182):dict(p=.229,spc=1.86,A=44.0,IP=3.19,PI=3.04,drv=12),('E5',31415):dict(p=.292,spc=1.77,A=45.8,IP=3.35,PI=2.85,drv=11),
('E6',27182):dict(p=.252,spc=2.07,A=36.2,IP=3.14,PI=4.68,drv=12),('E6',31415):dict(p=.321,spc=1.97,A=37.9,IP=3.30,PI=4.39,drv=11)}
W=dict(p=lambda c:.04,spc=lambda c:.15,A=lambda c:5.0,IP=lambda c:.10*c,PI=lambda c:.12*c,drv=lambda c:3.0)
def grade(k,c,m):
    w=W[k](c); lo,hi=c-w,c+w
    if lo<=m<=hi: return 'HIT'
    edge=lo if m<lo else hi; return 'PARTIAL' if abs(m-edge)<=0.25*abs(edge) else 'MISS'
tot={'HIT':0,'PARTIAL':0,'MISS':0}; rows=[]
for key,pr in P.items():
    m=R[key]; g={k:grade(k,pr[k],m[k]) for k in pr}
    for x in g.values(): tot[x]+=1
    rows.append((key,m,pr,g))
print('| run | p | per pair | A | IP/pair | PI/pair | drivable |\n|---|---|---|---|---|---|---|')
for key,m,pr,g in rows:
    print('| %s s%d | %.3f vs %.3f %s | %.2f vs %.2f %s | %.1f vs %.1f %s | %.2f vs %.2f %s | %.2f vs %.2f %s | %d vs %d %s |'%(key[0],key[1],m['p'],pr['p'],g['p'],m['spc'],pr['spc'],g['spc'],m['A'],pr['A'],g['A'],m['IP'],pr['IP'],g['IP'],m['PI'],pr['PI'],g['PI'],m['drv'],pr['drv'],g['drv']))
print(tot)
print()
print('| run | p | spc | IP | PI | drv | A | zero | fails |')
for e in CFG:
    for s in (16180,27182,31415):
        r=R[(e,s)]; bb=bars(r); print(e,s,'p %.3f spc %.2f A %.1f IP %.3f PI %.2f drv %d/%d zero %d PP %d | fails %s'%(r['p'],r['spc'],r['A'],r['IP'],r['PI'],r['drv'],r['n'],r['zero'],r['PP'],[k for k,v in bb.items() if not v]))
import statistics as st
print()
for e in CFG:
    rs=[R[(e,s)] for s in (16180,27182,31415)]
    print(e,'pooled mean (min-max):',' '.join('%s %.3g (%.3g-%.3g)'%(k,st.mean(r[k] for r in rs),min(r[k] for r in rs),max(r[k] for r in rs)) for k in ('p','spc','A','IP','PI','drv','PP')))
