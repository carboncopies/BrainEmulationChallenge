import json
d=json.load(open('it4_out.json')); ph=json.load(open('it4_phases.json'))['phases']
sp=d['phases'][0]['spikes']['SpikeTimes']
miss=0;tot=0;offs=[]
for t,gi,s in ph[0]['events']:
    for n in s:
        tt=sp.get(str(n),{}).get('tSpike_ms',[]); near=[x for x in tt if abs(x-t)<=3]
        tot+=1
        if not near: miss+=1; print('MISSING',t,n)
        else: offs.append(round(min(near,key=lambda x:abs(x-t))-t,2))
print('forced spikes found near expected time: %d/%d; offsets ms min %s max %s'%(tot-miss,tot,min(offs),max(offs)))
print('wall_s',round(d['wall_s'],1))
