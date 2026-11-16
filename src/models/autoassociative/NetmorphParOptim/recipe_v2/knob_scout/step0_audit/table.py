import json, datetime
R = json.load(open('results.json')); R.sort(key=lambda r:(r['label'], r['seed'], r['ctime']))
L = ['| label | seed | folder (first 8) | created | ints | attractor pyr/int dend. bif (pyr %) | IN axon: dist from centre / own soma, bands 0-40, 40-80, 80-120 | IN frac nodes r>120 | IN straight/path | PYR axon: dist from centre / own soma, bands | PYR frac r>120 | PYR straight/path |','|'+'---|'*12]
def b(x):
    s=[]
    for k in ('0-40','40-80','80-120'):
        v=x['bands'][k]; s.append('n/a' if v['n_cells']==0 else '%d/%d (n=%d)'%(round(v['median_dist_from_centre']),round(v['median_dist_from_own_soma']),v['n_cells']))
    return '; '.join(s)
for r in R:
    m=r['attractor_mix']; p=m.get('pyramidal',0); i=m.get('interneuron',0); I=r['interneuron']; P=r['pyramidal']
    L.append('| %s | %d | %s | %s | %d | %d/%d (%.0f%%) | %s | %.4f | %.2f | %s | %.4f | %.2f |'%(r['label'],r['seed'],r['folder'][:8],datetime.datetime.fromtimestamp(r['ctime']).strftime('%m-%d %H:%M'),r['n_int'],p,i,100*p/(p+i),b(I),I['frac_nodes_r_gt_120'],I['straight_over_path'],b(P),P['frac_nodes_r_gt_120'],P['straight_over_path']))
open('results_table.md','w').write('\n'.join(L)+'\n'); print('\n'.join(L))
