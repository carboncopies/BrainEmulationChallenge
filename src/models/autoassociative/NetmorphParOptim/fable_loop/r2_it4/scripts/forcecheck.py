import json,sys
X=sys.argv[1]; D='/home/johnjose/cos/netmorph_work/fable_loop/r2_it4/%s/'%X
d=json.load(open(D+'out.json')); ph=json.load(open(D+'phases.json'))['phases']
sp=d['phases'][0]['spikes']['SpikeTimes']
miss=0;tot=0;offs=[]
for t,gi,s in ph[0]['events']:
    for n in s:
        tt=sp.get(str(n),{}).get('tSpike_ms',[]); near=[x for x in tt if abs(x-t)<=3]
        tot+=1
        if not near: miss+=1; print('MISSING',t,n)
        else: offs.append(round(min(near,key=lambda x:abs(x-t))-t,2))
print('forced spikes found near expected time: %d/%d; offsets ms min %s max %s'%(tot-miss,tot,min(offs),max(offs)))
