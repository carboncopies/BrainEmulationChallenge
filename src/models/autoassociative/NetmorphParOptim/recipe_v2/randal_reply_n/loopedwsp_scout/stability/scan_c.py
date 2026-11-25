"""For every stored arm: scale ALL recurrent member conductances (AMPA and NMDA) by c, find per event the smallest c that (a) completes (non-cue members fire in 30 ms) and (b) ignites (member spikes in 450 ms > 50).
c*_comp, c*_ign are properties of the programmed matrix + cell model; the arm 'terminates after completing' iff c*_comp <= 1 < c*_ign (window contains the programmed c = 1)."""
import numpy as np, rn, glob, os, json
cs=np.round(np.arange(0.5,1.351,0.025),3)
out={}
runs=[('s77777_LH_r1_f1','rawB_'),('s66666_LH_r1_f1','rawB_'),('s77777_W70_r1_f1','rawC_'),('s66666_W70_r1_f1','rawC_'),('s77777_W50_r1_f1','rawC_'),('s66666_W50_r1_f1','rawC_'),('s77777_H2_r1_f1','rawC_'),('s77777_L0_r1_f1','rawB_'),('s66666_L0_r1_f1','rawB_')]
for tag,pre in runs:
    d=rn.load_run(tag,pre); A=d['A']; M=rn.member_matrices('s%d'%d['seed'],d['arm'],A,d['r']); cl,meta=rn.events_cues(d,A)
    sel=[i for i,e in enumerate(meta) if e['kind'] in ('full','p75','p50')]; ms=[meta[i] for i in sel]; cc=[cl[i] for i in sel]
    comp=np.zeros((len(cs),len(sel)),bool); ign=np.zeros_like(comp)
    for a,c in enumerate(cs):
        R=rn.sim(M['XA']*c,M['XN']*c,cc); mm=rn.sim_measures(R,ms,A)
        comp[a]=[x['complete'] for x in mm]; ign[a]=[x['mem450']>50 for x in mm]
    def first(col):
        w=np.where(col)[0]; return float(cs[w[0]]) if len(w) else None
    rec=dict(kinds=[m['kind'] for m in ms],c_comp=[first(comp[:,j]) for j in range(len(sel))],c_ign=[first(ign[:,j]) for j in range(len(sel))],
             rho_A=float(max(abs(np.linalg.eigvals(M['XA'])))),rho_N=float(max(abs(np.linalg.eigvals(M['XN'])))),colsum_A=float(M['XA'].sum(0).mean()),colsum_N=float(M['XN'].sum(0).mean()),bg_in=float(M['bg_in'].mean()))
    out[tag]=rec; print(tag,'rhoA %.1f rhoN %.1f'%(rec['rho_A'],rec['rho_N']));
    for k in ('full','p75','p50'):
        ix=[j for j,x in enumerate(rec['kinds']) if x==k]; print('   %s c_comp'%k,[rec['c_comp'][j] for j in ix],'c_ign',[rec['c_ign'][j] for j in ix],flush=True)
    json.dump(out,open('scan_c.json','w'))
