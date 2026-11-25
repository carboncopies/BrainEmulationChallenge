import numpy as np, time, statistics as st, sys
import rn
def summarize(rows):
    out={}
    for k in ['full','p75','p50','p25','p1','unrel']:
        q=[r for r in rows if r['kind']==k and not r.get('cont',False)]
        if not q: continue
        out[k]=(sum(r['complete'] for r in q),sum(r['recruit'] for r in q),sum(r['reverb'] for r in q),len(q),st.median(r['mem450'] for r in q),st.median(r['last'] for r in q))
    return out
def show(name,s): print(name,' | '.join('%s c%d rec%d rv%d/%d m450=%.0f last=%.0f'%((k,)+v) for k,v in s.items()))
if __name__=='__main__':
    tag,prefix,arm,key=sys.argv[1:5]; kappa=float(sys.argv[5])
    d=rn.load_run(tag,prefix); A=d['A']; M=rn.member_matrices(key,arm,A,d['r']); cl,meta=rn.events_cues(d,A)
    show('STORED',summarize(rn.stored_measures(d,A)))
    t=time.time(); R=rn.sim(M['XA'],M['XN'],cl,kappa=kappa); print('sim %.1fs'%(time.time()-t))
    show('MODEL k=%g'%kappa,summarize(rn.sim_measures(R,meta,A)))
