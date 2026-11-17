import json,sys,numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); import recipelib as L
pv=json.load(open('pv_results.json'))
for k,v in sorted(pv.items()):
    D=L.Dump('grow_%s/viz/sample_0000.json'%k); P=D.G[:96,:96]; nz=(P>0).sum(); 
    print(k,'int',v['n_int'],'Pyr->Pyr syn',v['pyr_pyr'],'p',round(nz/9120,3),'spc',round(v['pyr_pyr']/nz,2),'| A',round(v['inhib_frac_ip_over_ip_pp'],3),'| IP/pair',v['syn_per_pair_int_pyr'],'PI/pair',v['syn_per_pair_pyr_int'],'II/pair',v['syn_per_pair_int_int'],'| drv8',v['drivable_8cell_capaware'],'simple',v['drivable_simple'],'zero',v['zero_pyr_input'],'| IP',v['int_pyr'],'PI',v['pyr_int'],'II',v['int_int'],'tg/int',v['pyr_targets_per_int_mean'],'IPprob',round(v['pairs_int_pyr']/(v['n_int']*96),3),'PIprob',round(v['pairs_pyr_int']/(96*v['n_int']),3))
