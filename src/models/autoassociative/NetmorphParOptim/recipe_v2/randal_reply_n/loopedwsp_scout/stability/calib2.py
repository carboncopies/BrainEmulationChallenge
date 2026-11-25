import numpy as np, rn, json, statistics as st
d=rn.load_run('s77777_LH_r1_f1','rawB_'); A=d['A']; M=rn.member_matrices('s77777','LH',A,1.0); cl,meta=rn.events_cues(d,A)
sm=rn.stored_measures(d,A); sel=[i for i,e in enumerate(meta) if e['kind'] in ('p75','p50','full') and not sm[i]['cont']]
tg_m=st.median(sm[i]['mem450'] for i in sel); tg_l=st.median(sm[i]['last'] for i in sel); print('targets mem450 %.0f last %.0f'%(tg_m,tg_l))
res=[]
for n in (1.0,0.9,0.8,0.7,0.6,0.5):
  for gIP in (0.,0.25,0.5,1.0):
    XA,XN,XG=rn.full_matrices(M,7,1.0,gIP); XN=XN.copy(); XN*=n
    R=rn.sim(XA,XN,[cl[i] for i in sel],XG=XG,npyr=17); mm=rn.sim_measures(R,[meta[i] for i in sel],A)
    m=st.median(x['mem450'] for x in mm); l=st.median(x['last'] for x in mm)
    loss=(np.log((m+5)/(tg_m+5)))**2+(np.log((l+5)/(tg_l+5)))**2; res.append((float(loss),n,gIP,m,l)); print('nmda x%.1f gIP %.2f mem450 %.0f last %.0f loss %.3f'%(n,gIP,m,l,loss),flush=True)
res.sort(); print('BEST',res[:3]); json.dump(res,open('calib2.json','w'))
