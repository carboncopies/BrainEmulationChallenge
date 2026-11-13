import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
nP=96; NI=48
Gpi=G[:nP,nP:]; pairs=Gpi[Gpi>0]; n=pairs/0.98
out={}
out['n_pairs']=int(len(pairs)); out['n_syn']=float(n.sum()); out['syn_per_pair_mean']=float(n.mean())
out['p_PyrInt']=float((Gpi>0).mean()); out['pyr_in_per_int_mean_pairs']=float((Gpi>0).sum(0).mean()); out['syn_in_per_int_mean']=float(n.sum()/NI)
def st(u): return dict(mean=float(u.mean()),median=float(np.median(u)),p90=float(np.percentile(u,90)),max=float(u.max()),frac_above_3x_nat=float((u>3*0.85).mean()),n_above_3x_nat=int((u>3*0.85).sum()),pctile_of_2p55=float((u<=2.55).mean()*100))
out['now_unitary_nS_w1']=st(pairs)           # R3: weight 1 => conductance = g_peak_sum
out['now_unitary_nS_w0.2_asgrown']=st(0.2*pairs)
s_nat=0.85/pairs.mean(); out['scale_mean_to_0.85']=float(s_nat); out['scale_median_to_0.85']=float(0.85/np.median(pairs))
for s,nm in [(s_nat,'natural_mean'),(1.0,'x1_now'),(3*0.85/pairs.mean(),'3x_natural_mean')]: out['scaled_'+nm]=dict(scale=float(s),**st(pairs*s))
# drivable counts: per interneuron, total input from the best 8 pyr cells (cap-aware: conductance per cell-pair = s*g, thr 13.84 nS)
THR=13.84
def best8(s):
    c=0; sums=[]
    for k in range(NI):
        v=np.sort(Gpi[:,k])[::-1][:8]*s; sums.append(v.sum())
    sums=np.array(sums); return int((sums>=THR).sum()),sums
for s,nm in [(s_nat,'natural_mean'),(1.0,'x1_now'),(3*0.85/pairs.mean(),'3x_natural_mean')]:
    c,sm=best8(s); out['int_drivable_best8_'+nm]=dict(scale=float(s),n=c,top_sums=[round(float(x),1) for x in np.sort(sm)[::-1][:12]])
json.dump(out,open('natural_check.json','w'),indent=1); print(json.dumps(out,indent=1))
