import json,glob
rows=[]
for f in sorted(glob.glob('raw_*.json')):
    d=json.load(open(f))
    if d.get('mode','single')!='single':
        rows.append(dict(tag=d['tag'],mode=d['mode'],sg=int(d['sg']),success=d['success'],complete=[o['noncue_fired'] for o in d['ripple']],tot=[o['noncue_total'] for o in d['ripple']],ct=len(d['crosstalk']),spur=d['spurious_spikes'],last=d['last_spike_ms'])); continue
    ev=d['events']; K=len(d['groups']); ok=0;full=0;f3=0;lat=[]
    for g in range(K):
        e=ev[3*g:3*g+3]; ok+=all(x['clean'] for x in e); full+=e[0]['noncue_fired']==e[0]['noncue_total']; f3+=sum(x['noncue_fired']>0 for x in e[1:])
        if e[0]['latency_ms'] is not None: lat.append(e[0]['latency_ms'])
    rows.append(dict(tag=d['tag'],net=d['seed'],design=d['design'],c=d['c'],sg=int(d['sg']),K=K,ok=ok,full=full,false3=f3,spur=sum(x['n_other_pyr_spikes'] for x in ev),ints=sum(x['interneuron_spikes'] for x in ev),maxlat=max(lat) if lat else None))
json.dump(rows,open('summary.json','w'),indent=1)
for r in sorted([r for r in rows if 'K' in r],key=lambda r:(r['net'],r['design'],r['c'],r['sg'])): print(r['net'],r['design'],r['c'],'SG' if r['sg'] else 'on','K',r['K'],'ok',r['ok'],'full',r['full'],'f3',r['false3'],'spur',r['spur'],'ints',r['ints'],r['maxlat'])
for r in rows:
    if 'mode' in r: print(r)
