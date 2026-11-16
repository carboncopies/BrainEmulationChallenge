import json,glob
rows=[]
for f in sorted(glob.glob('raw_*.json')):
    d=json.load(open(f)); ev=d['events']; K=len(d['groups']); mem_ok=0; full=0; false3=0; spur=0; ints=0; lat=[]; ovs=0
    for g in range(K):
        e=ev[3*g:3*g+3]
        mem_ok+=all(x['clean'] for x in e)
        full+=e[0]['noncue_fired']==e[0]['noncue_total']
        false3+=sum(x['noncue_fired']>0 for x in e[1:])
        if e[0]['latency_ms'] is not None: lat.append(e[0]['latency_ms'])
    spur=sum(x['n_other_pyr_spikes'] for x in ev); ints=sum(x['interneuron_spikes'] for x in ev); 
    rows.append(dict(tag=d['tag'],seed=d['seed'],design=d['design'],c=d['c'],sg=int(d['sg']),K=K,mem_ok=mem_ok,full=full,false3=false3,spur=spur,ints=ints,lat=lat,maxfullints=max(x['interneuron_spikes'] for x in ev[0::3]),endmax=max([x['burst_end_ms'] or 0 for x in ev[0::3]])))
json.dump(rows,open('summary.json','w'),indent=1)
print('seed design c sg | K mem_ok full false3 spur_pyr_spikes int_spikes maxlat')
for r in sorted(rows,key=lambda r:(r['seed'],r['design'],r['c'],r['sg'])):
    print(r['seed'],r['design'],r['c'],'SG' if r['sg'] else 'on','|',r['K'],r['mem_ok'],r['full'],r['false3'],r['spur'],r['ints'],max(r['lat']) if r['lat'] else None, r['maxfullints'])
