import json, numpy as np
d=json.load(open('scan_c.json')); rows=['| run | rho(AMPA member matrix) nS | rho(NMDA) nS | median c_ign, 75% cues | median c_comp, 75% | median c_ign, 50% | median c_comp, 50% | margin at c=1: ignites in n of 6 p75 events (c_ign <= 1) | completes without igniting (c_comp <= 1 < c_ign) |','|'+'---|'*9]
def med(v): 
    v=[x for x in v if x is not None]; return '%.3f'%np.median(v) if v else '>1.35'
for tag,r in d.items():
    k=r['kinds']; ix=lambda kk:[j for j,x in enumerate(k) if x==kk]
    ci=[r['c_ign'][j] for j in ix('p75')]; cc=[r['c_comp'][j] for j in ix('p75')]
    ign=sum(1 for c in ci if c is not None and c<=1.0+1e-9); win=sum(1 for a,b in zip(cc,ci) if a is not None and a<=1.0+1e-9 and (b is None or b>1.0+1e-9))
    rows.append('| %s | %.1f | %.1f | %s | %s | %s | %s | %d/6 | %d/6 |'%(tag,r['rho_A'],r['rho_N'],med(ci),med(cc),med([r['c_ign'][j] for j in ix('p50')]),med([r['c_comp'][j] for j in ix('p50')]),ign,win))
open('scan_table.md','w').write('\n'.join(rows)+'\n'); print('\n'.join(rows))
