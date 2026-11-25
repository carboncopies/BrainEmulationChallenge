import json, numpy as np, collections
R=json.load(open('stage1_runs.json')); rr=json.load(open('stage1_random.json'))
tab=collections.defaultdict(dict)
for r in R: tab[(r['k'],r['H'],r['ov'])][r['key']]=max(r['M'])
lines=['# Stage 1 results table (auto)', '', 'M(k) = max over 3 packing orderings; median over 10 models; n>=1 / n>=2 = number of models with at least 1 / 2 held assemblies', '', '| k | active % | H (cap) | overlap | median M | models M>=1 | models M>=2 | per-model M |','|---|---|---|---|---|---|---|---|']
for k in (6,8,12,17,20,25):
    for H in (None,5.0,3.0,2.0,1.5):
        for ov in ('o0','ov'):
            v=[tab[(k,H,ov)][key] for key in sorted(tab[(k,H,ov)])]
            lines.append('| %d | %.1f | %s | %s | %s | %d | %d | %s |'%(k,100*k/96,'none' if H is None else '%.1fT'%H,ov,np.median(v),sum(x>=1 for x in v),sum(x>=2 for x in v),v))
lines+=['','Random allocation control (uniform random k-sets held standalone at H=3T, 5000 per model):','','| k | mean | max over models |','|---|---|---|']
for k in (6,8,12,17,20,25):
    v=[x['rand_held'] for x in rr if x['k']==k]; lines.append('| %d | %.4f | %.4f |'%(k,np.mean(v),np.max(v)))
open('results_stage1.md','w').write('\n'.join(lines)); print('\n'.join(lines))
