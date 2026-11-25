import sys, json, glob
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import analyze_d as AD, analyze_nr as AN
H='/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_tests/'
S={}
for d in ['BASE','W13','LPS','CASC','RN','E20']:
  for s in [66666,77777]:
    sm,rows=AD.summ(H+'rawP2_P2_%s_s%d.json'%(d,s))
    sm['PASS_T50']=bool(sm['PASS75'] and sm['p50'][0]>=3)
    S['%s_s%d'%(d,s)]=sm
    print(d,s,'rho%.2f'%sm['rho'],'full',sm['full'],'75',sm['p75'],'50',sm['p50'],'25rec',sm['p25_recruit'],'1',sm['p1_recruit'],'unr',sm['unrel_recruit'],'med/max',AN.f(sm['median_last']),AN.f(sm['max_last']),'stops',sm['stops100'],'nonmem',sm['events_nonmember'],'cont',sm['contaminated'],'maxin',sm['max_member_input'],'over3T',sm['members_over_3T'],'maxpair',round(sm['max_pair'],2),'P75',sm['PASS75'],'PT',sm['PASS_T50'])
    print('   missing75',sm['missing75'])
json.dump(S,open(H+'p2_summary.json','w'),indent=1,default=str)
