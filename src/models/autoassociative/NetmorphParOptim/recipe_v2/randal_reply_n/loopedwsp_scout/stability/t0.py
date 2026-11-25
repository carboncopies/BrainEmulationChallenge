import numpy as np, json, time
import rn
for tag,prefix,arm,key in [('s77777_LH_r1_f1','rawB_','LH','s77777'),('s66666_LH_r1_f1','rawB_','LH','s66666'),('s77777_W70_r1_f1','rawC_','W70','s77777'),('s66666_W70_r1_f1','rawC_','W70','s66666')]:
    d=rn.load_run(tag,prefix); A=d['A']; M=rn.member_matrices(key,arm,A)
    fl=d['flags']['member_input_nS']; mine=M['member_input']
    diff=max(abs(mine[i]-fl[str(c)]) for i,c in enumerate(A))
    print(tag,'max |col-sum - stored member_input| =%.3f'%diff,'n pairs',(M['XA']>0).sum(),'stored n_programmed',d['flags']['n_programmed'],'mean in-assembly AMPA col sum %.1f NMDA %.1f bg %.1f'%(M['XA'].sum(0).mean(),M['XN'].sum(0).mean(),M['bg_in'].mean()), 'lam_max AMPA %.2f'%max(abs(np.linalg.eigvals(M['XA']))))
