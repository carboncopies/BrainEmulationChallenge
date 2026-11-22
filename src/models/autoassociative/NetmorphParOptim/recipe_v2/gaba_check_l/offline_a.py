#!/usr/bin/env python3
"""Offline analysis (no NES): (1) GABA geometry per E4 model, (2) interneuron firing/timing and GABA conductance reaching targets in the 294 existing ripple_overlap_j sims (raw spikes)."""
import sys, json, glob, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); sys.path.insert(0,'.')
import recipelib as L, ovlib as O
from nesmodel import kern
R='/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/'
NP=96; W=0.2; GSYN=0.8
geo={}; GAS={}
for key,m in O.MODELS.items():
    D=L.Dump(m['dump']); GA=D.GA[NP:, :NP]*W        # pair conductance nS, Int(20) x Pyr(96) = weight*g_peak_sum
    GAS[key]=(D, GA)
    nsyn=D.GA[NP:, :NP]/GSYN
    has=GA>0
    per_pyr_sum=GA.sum(0); per_pyr_n=has.sum(0)
    geo[key]=dict(int_pyr_pairs=int(has.sum()), pairs_per_pyr_mean=float(per_pyr_n.mean()), pyr_with_no_gaba=int((per_pyr_n==0).sum()),
       syn_per_pair_mean=float(nsyn[has].mean()), pair_g_mean=float(GA[has].mean()), pair_g_max=float(GA.max()),
       ceiling_sum_mean=float(per_pyr_sum.mean()), ceiling_sum_p90=float(np.percentile(per_pyr_sum,90)), ceiling_sum_max=float(per_pyr_sum.max()),
       int_to_pyr_out_mean=float(has.sum(1).mean()), n_int=int(GA.shape[0]))
    # Int->Int
json.dump(geo,open('geometry.json','w'),indent=1)
print('GEOMETRY'); 
for k,v in geo.items(): print(k,{a:round(b,3) if isinstance(b,float) else b for a,b in v.items()})
# ---- events
DEL=1.0
def gaba_g(key, post, ispikes, t):
    """GABA conductance (nS) on Pyr post at time t from interneuron spikes dict {int_index(0..19): [times]}, kernel rise .5 decay 10, delay DEL"""
    D,GA=GAS[key]; g=0.0
    for i,ts in ispikes.items():
        gp=GA[i,post]
        if gp<=0: continue
        for s in ts:
            if s+DEL<=t: g+=gp*float(kern(t-s-DEL,0.5,10.0))
    return g
rows=[]
for fn in sorted(glob.glob(R+'raw_*.json')):
    d=json.load(open(fn)); key=d['key']
    if d['mode']!='ov' : continue
    if not any(e['label'] in('full',) for e in d['events']): continue
    sp={int(k):v for k,v in d['spikes'].items()}; grp=d['groups']
    allmem={m for g in grp for m in g['members']}
    for e in d['events']:
        if e['label']!='full': continue
        t0=e['t']; g=grp[e['group']]; win=lambda i:[x-t0 for x in sp.get(i,[]) if t0<=x<t0+100]
        nc=g['noncue']; first_nc=min([x for m in nc for x in win(m)],default=None)
        cue_on=0.0
        isp={i-NP:win(i) for i in range(NP,NP+20) if win(i)}
        first_int=min([x for v in isp.values() for x in v],default=None)
        n_int=len(isp); n_ispk=sum(len(v) for v in isp.values())
        # inhibition on non-cue members at their first spike time (GABA on or off in this run: hypothetical conductance with GABA on)
        gat=[]; 
        for m in nc:
            w=win(m)
            if w: gat.append(gaba_g(key,m,{i:[t0+x for x in v] for i,v in isp.items()},t0+w[0]))
        # ceiling at that time if all interneurons connected to m fired together just before: sum of pair g
        D,GA=GAS[key]; ceil=[float(GA[:,m].sum()) for m in nc]
        # non-member Pyr that fired (spurious): hypothetical GABA at its first spike
        spur=[i for i in range(NP) if i not in allmem and win(i)]
        sg=[]
        for i in spur:
            sg.append(gaba_g(key,i,{j:[t0+x for x in v] for j,v in isp.items()},t0+win(i)[0]))
        rows.append(dict(key=key,tag=d['tag'],c=d['c'],sg=int(d['sg']),group=e['group'],n_int_fired=n_int,n_int_spikes=n_ispk,first_int_ms=first_int,first_nc_ms=first_nc,
            int_before_nc=(None if first_int is None or first_nc is None else bool(first_int+DEL<first_nc)),
            gaba_at_nc_first=gat, ceil_nc=ceil, n_spur=len(spur), gaba_at_spur=sg))
json.dump(rows,open('offline_events.json','w'))
import statistics as S
def sel(**kw): return [r for r in rows if all(r[k]==v for k,v in kw.items())]
print('EVENTS full-cue',len(rows))
for c in (0,0.15,1.5):
  for sg in (0,1):
    R_=sel(c=c,sg=sg); a=[r for r in R_ if r['first_int_ms'] is not None]; nci=[r for r in R_ if r['first_nc_ms'] is not None]
    fi=[r['first_int_ms'] for r in a]; fn_=[r['first_nc_ms'] for r in nci]
    ib=[r['int_before_nc'] for r in R_ if r['int_before_nc'] is not None]
    g_=[x for r in R_ for x in r['gaba_at_nc_first']]; cl=[x for r in R_ for x in r['ceil_nc']]
    print('c',c,'sg',sg,'events',len(R_),'with int spikes',len(a),'median n_int',S.median([r['n_int_fired'] for r in R_]) if R_ else None,
      'first_int med %.2f'%S.median(fi) if fi else '', 'first_nc med %.2f'%S.median(fn_) if fn_ else '', 'int_before_nc %d/%d'%(sum(ib),len(ib)),
      'gaba@nc median %.3f p90 %.3f max %.3f'%(np.median(g_),np.percentile(g_,90),max(g_)) if g_ else '', 'ceil median %.2f max %.2f'%(np.median(cl),max(cl)) if cl else '')
sp_=[x for r in rows for x in r['gaba_at_spur']]
print('spurious non-member Pyr first spikes:',len(sp_),'hypothetical GABA at that time median %.3f p90 %.3f max %.3f'%(np.median(sp_),np.percentile(sp_,90),max(sp_)) if sp_ else '')
for sg in (0,1):
    x=[v for r in sel(sg=sg) for v in r['gaba_at_spur']]; print('sg',sg,'n spurious cells',len(x),'median',np.median(x) if x else None,'max',max(x) if x else None)
