import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
import recipelib as L
from gabafile import *
D=L.Dump('/home/johnjose/cos/netmorph_work/recipe_v2/dendrite_rerun/grow_S1/viz/sample_0000.json')
NP,NI=len(D.pyr),len(D.its); print('Pyr',NP,'Int',NI)
cls,h,off,rec=load('/var/lib/BrainGenix/NES/Admonishing/Models/v2-arbor-S10000')
ng=int((rec['NT']==1).sum()); print('GABA records',ng,'dump GABA synapses (sum g/0.8)',round(D.GA.sum()/0.8,1),'AMPA recs',int((rec['NT']==0).sum()),'dump AMPA syn',round(D.G.sum()/0.98,1))
P=np.array(D.pyr); I=np.array(D.its)
out={}
GA=D.GA; G=D.G
def stats(M,name):
    nz=M[M>0]; n=nz/0.8
    return dict(n_pairs=int(len(nz)),n_syn_total=float(n.sum()),n_syn_per_pair_mean=float(n.mean()),n_syn_per_pair_min=float(n.min()),n_syn_per_pair_max=float(n.max()),n_syn_hist={int(k):int(v) for k,v in zip(*np.unique(np.round(n).astype(int),return_counts=True))})
ip=GA[np.ix_(I,P)]; ii=GA[np.ix_(I,I)]; pp_ga=GA[np.ix_(P,np.arange(len(G)))].sum()
out['Int->Pyr']=stats(ip,'ip'); out['Int->Int']=stats(ii,'ii'); out['GABA_from_Pyr_pre']=float(pp_ga)
out['p_Int->Pyr']=float((ip>0).sum()/(NI*NP)); 
pi=G[np.ix_(P,I)]; out['p_Pyr->Int_AMPA']=float((pi>0).sum()/(NP*NI)); out['p_Int->Int']=float((ii>0).sum()/(NI*(NI-1)))
pp=G[np.ix_(P,P)]; out['p_Pyr->Pyr_AMPA']=float((pp>0).sum()/(NP*(NP-1)))
# unitary conductance per pair now = weight*0.8*n = 0.16*n ; peak sum cap = 0.8 n
for f in [1,2,5]:
    u=0.2*f*ip[ip>0]  # nS (weight*gsum)
    out['unitary_nS_x%d'%f]=dict(mean=float(u.mean()),median=float(np.median(u)),p10=float(np.percentile(u,10)),p90=float(np.percentile(u,90)),max=float(u.max()),min=float(u.min()),frac_above_0p65=float((u>0.65).mean()),frac_above_3=float((u>3).mean()))
# per Pyr target: total inhibitory conductance input and number of inhibitory synapses/cell
nsyn_per_pyr=ip.sum(axis=0)/0.8
out['GABA_syn_per_pyr_mean']=float(nsyn_per_pyr.mean()); out['GABA_syn_per_pyr_min_max']=[float(nsyn_per_pyr.min()),float(nsyn_per_pyr.max())]
out['n_Int_inputs_per_pyr_mean']=float(((ip>0).sum(axis=0)).mean())
out['AMPA_pyr_syn_in_per_pyr_mean']=float(pp.sum(axis=0).mean()/0.98)
# natural-bound factor: factors making mean / median / max unitary equal 0.65 nS
u1=0.16*(ip[ip>0]/0.8)
out['factor_mean_eq_0.65']=0.65/float(u1.mean()); out['factor_median_eq_0.65']=0.65/float(np.median(u1)); out['factor_max_eq_0.65']=0.65/float(u1.max()); out['factor_max_eq_3nS']=3.0/float(u1.max())
out['factor_mean_eq_0.65_note']='pair g = weight*0.8*n; 0.65 nS Ecker is per-connection IPSC peak for the PVBC->PC (which in Ecker has several contacts; n per connection not reported)'
json.dump(out,open('natural_range.json','w'),indent=1)
print(json.dumps(out,indent=1))
