import json
d=json.load(open('r2it1_out.json')); ph=json.load(open('r2it1_phases.json'))['phases']
sp=d['phases'][0]['spikes']['SpikeTimes']
miss=0;tot=0;devs=[]
for t,gi,J,cs in ph[0]['events']:
    for n,off in cs:
        tt=sp.get(str(n),{}).get('tSpike_ms',[]); exp=t+off
        near=[x for x in tt if abs(x-exp)<=3]; tot+=1
        if not near: miss+=1; print('MISSING',exp,n)
        else: devs.append(round(min(near,key=lambda x:abs(x-exp))-exp,3))
print('forced spikes found at expected absolute time (+-3ms search): %d/%d; deviation ms min %s max %s; max abs %s'%(tot-miss,tot,min(devs),max(devs),max(abs(x) for x in devs)))
print('wall_s',round(d['wall_s'],1))
