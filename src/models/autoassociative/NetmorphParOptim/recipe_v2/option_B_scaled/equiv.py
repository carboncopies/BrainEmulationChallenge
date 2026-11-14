import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
R='/home/johnjose/cos/netmorph_work/recipe_v2/'
out={}
for nm,p in (('S1',R+'dendrite_rerun/grow_S1/viz/sample_0000.json'),('seed629',R+'robustness_S1/grow_S1-seed629/viz/sample_0000.json')):
    D=L.Dump(p); G=D.G; GA=D.GA; P=96; its=list(range(P,D.N))
    pi=G[:P,P:]; ip=GA[P:,:P]; ii=GA[P:,P:]
    inpyr=lambda gx:(0.2*gx*ip).sum(0)                  # inhibitory conductance onto each pyramid (sum of unitary peak, nS)
    r=dict(pi_pairs=int((pi>0).sum()),pi_mean_pair_nS_R3=float(pi[pi>0].mean()),pi_inputs_per_int=float((pi>0).sum(0).mean()),
           ip_pairs=int((ip>0).sum()),ip_mean_pair_nS_default=float((0.2*ip[ip>0]).mean()),ip_inputs_per_pyr=float((ip>0).sum(0).mean()),
           ii_pairs=int((ii>0).sum()))
    for s in (1,3,5,7,10,20): 
        tot=(pi*s).sum(0); r['int_input_total_nS_s%d'%s]=dict(mean=float(tot.mean()),median=float(np.median(tot)),max=float(tot.max()),mean_pair=float((pi[pi>0]*s).mean()),x_natural_pair=float((pi[pi>0]*s).mean()/0.85))
    for gx in (1,2.5,5,10):
        t=inpyr(gx); r['pyr_inh_total_nS_g%g'%gx]=dict(mean=float(t.mean()),median=float(np.median(t)),max=float(t.max()),mean_pair=float((0.2*gx*ip[ip>0]).mean()),x_natural_pair=float((0.2*gx*ip[ip>0]).mean()/0.65))
    out[nm]=r
lit=dict(PVBC_to_PC_unitary_nS=0.65,PC_to_PVBC_unitary_nS=0.85,PVBC_inputs_per_PC=37.5,PC_inputs_per_PVBC_derived=800)
lit['PVBC_inh_total_per_PC_nS_derived']=lit['PVBC_to_PC_unitary_nS']*lit['PVBC_inputs_per_PC']; lit['PC_drive_total_per_PVBC_nS_derived']=lit['PC_to_PVBC_unitary_nS']*lit['PC_inputs_per_PVBC_derived']
out['literature']=lit
json.dump(out,open('equivalents.json','w'),indent=1)
for k,v in out.items(): print(k,json.dumps(v)[:1800])
