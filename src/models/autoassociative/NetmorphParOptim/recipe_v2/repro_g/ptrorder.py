import re,glob,json,itertools
W='/home/johnjose/cos/netmorph_work/recipe_v2'
def pdir(folder,key):
    d=json.load(open(W+'/%s/pv_results.json'%folder))[key]['dir']
    for b in ('/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/','/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'):
        g=glob.glob(b+d+'/*_report')
        if g: return g[0]
def order(rep):
    m={}
    for l in open(rep):
        r=re.match(r'^(\d+)\((\d+)\) -> (\d+)\((\d+)\)',l)
        if r: m[int(r.group(2))]=int(r.group(1)); m[int(r.group(4))]=int(r.group(3))
    return [i for i,p in sorted(m.items(),key=lambda x:x[1])]
R=[('V1_s27182','pv_arbor_seeds','A'),('V1_s27182_d015','pv_dsyn015','B'),('V1_s27182_fix','linefix_b','B'),
   ('V1n30_s27182_p0d0175_i0d0495','linefix_c','A'),('V1n30_s27182_p0d035_i0d0495','capacity_d','B'),('V1n30_s27182_p0d05_i0d0495','capacity_d','B'),
   ('V1n30_s16180_fix','linefix_b','A'),('V1n30_s16180_p0d0175_i0d0495','linefix_c','A'),('V1n30_s16180_p0d035_i0d0495','capacity_d','A'),('V1n30_s16180_p0d05_i0d0495','capacity_d','B'),
   ('V1n30_s31415_fix','linefix_b','A'),('V1n30_s31415_p0d0175_i0d0495','linefix_c','B')]
O={}
for key,folder,arb in R:
    rep=pdir(folder,key)
    if rep: O[key]=(order(rep),arb)
for g in ('V1_s27182','V1n30_s27182','V1n30_s16180','V1n30_s31415'):
    ks=[k for k in O if k.startswith(g)]
    print(g)
    for a,b in itertools.combinations(ks,2):
        print('  %-30s vs %-30s same-arbor-class %-5s identical pointer order %s'%(a[-24:],b[-24:],O[a][1]==O[b][1],O[a][0]==O[b][0]))
