"""Bars 1-7 per model. usage as module: metrics(key, results_json, grow_dir_parent) ; CLI: bars.py -> bars_table.json for the 6 existing models (+ new ones if present in pv_results.json here)."""
import json,sys,os,statistics as st
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); import recipelib as L
W='/home/johnjose/cos/netmorph_work/recipe_v2/'
def metrics(key,rj,gp):
    v=json.load(open(rj))[key]; D=L.Dump(gp+'/grow_%s/viz/sample_0000.json'%key); nz=int((D.G[:96,:96]>0).sum()); n=v['n_int']
    m=dict(key=key,dir=v['dir'],n_int=n,p=nz/9120,spc=v['pyr_pyr']/nz,A=100*v['inhib_frac_ip_over_ip_pp'],IP=v['int_pyr']/v['pairs_int_pyr'],PI=v['pyr_int']/v['pairs_pyr_int'],drv=v['drivable_8cell_capaware'],zero=v['zero_pyr_input'],PP=v['pyr_pyr'],ia=v['int_axon_len']['len_mean'],bio=v['bio_check'])
    thr=(n+2)//3 if n%3 else n//3   # one third, rounded up: 10 of 30, 7 of 20
    b={1:0.1<=m['p']<=0.3,2:1.9<=m['spc']<=4.5,3:4<=m['IP']<=9,4:1.5<=m['PI']<=4.5,5:m['drv']>=thr,6:m['bio']=='pass',7:25<=m['A']<=50}
    m['bars']=b; m['fails']=[k for k,x in b.items() if not x]; m['all7']=not m['fails']; m['drv_thr']=thr
    return m
OLD=[('E4',16180,'inhib_e','V1n20_s16180_p0d0175_i0d03'),('E4',27182,'inhib_f','V1n20_s27182_p0d0175_i0d03'),('E4',31415,'inhib_f','V1n20_s31415_p0d0175_i0d03')]
if __name__=='__main__':
    out=[]
    for rec,seed,folder,key in OLD:
        m=metrics(key,W+folder+'/pv_results.json',W+folder); m.update(recipe=rec,seed=seed,folder=folder); out.append(m)
    # E4 from headline_h (5 models) and the five new seeds here
    H=W+'headline_h'
    for s in (11111,22222):
        key='V1n20_s%d_p0d0175_i0d03'%s; m=metrics(key,H+'/pv_results.json',H); m.update(recipe='E4',seed=s,folder='headline_h'); out.append(m)
    for s in (33333,44444,55555,66666,77777):
        key='V1n20_s%d_p0d0175_i0d03'%s
        if os.path.exists('pv_results.json') and key in json.load(open('pv_results.json')):
            m=metrics(key,'pv_results.json','.'); m.update(recipe='E4',seed=s,folder='headline_i'); out.append(m)
    json.dump(out,open('bars_table.json','w'),indent=1,default=float)
    for m in out: print('%-6s s%-5d p %.3f spc %.2f A %.1f IP %.3f PI %.2f drv %d/%d zero %d PP %d fails %s'%(m['recipe'],m['seed'],m['p'],m['spc'],m['A'],m['IP'],m['PI'],m['drv'],m['n_int'],m['zero'],m['PP'],m['fails']))
