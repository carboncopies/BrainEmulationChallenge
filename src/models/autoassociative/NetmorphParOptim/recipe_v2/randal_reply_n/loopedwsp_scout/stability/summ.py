import statistics as st
def summarize(rows):
    out={}
    for k in ['full','p75','p50','p25','p1','unrel']:
        q=[r for r in rows if r['kind']==k and not r.get('cont',False)]
        if not q: continue
        out[k]=(sum(r['complete'] for r in q),sum(r['recruit'] for r in q),sum(r['reverb'] for r in q),len(q),st.median(r['mem450'] for r in q),st.median(r['last'] for r in q))
    return out
