"""usage: batch.py ROUNDNAME  -- runs job list for a round with <=2 concurrent NES sims, creates/deletes patched model copies."""
import sys, subprocess, itertools, os, json
from concurrent.futures import ThreadPoolExecutor
import patch_B
H='/home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled/'; PY=open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3/pypath').read().strip()
BGW=0.5
def rounds(r):
    J=[]  # (tag, s, gx, bgw, c, sg, kind, env)
    if r=='R1':  # background scan, ripple 12 ms, SG vs on
        CS=[0.5,1.0,1.5,1.75,1.85,2.0,2.5,3.0]
        for c in CS:
            J.append((f'bg_c{c}_SG',1,1,BGW,c,1,'rip:0123:12:1'))
            for s,gx in [(1,1),(3,5),(5,5),(7,5),(10,5),(10,10)]:
                J.append((f'bg_c{c}_s{s}_g{gx}',s,gx,BGW,c,0,'rip:0123:12:1'))
    if r=='R2':  # recall at natural-cap background c=0.15 and ripple tests for each scaled condition
        for s,gx in [(1,1),(3,5),(5,5),(7,5),(10,5),(10,10)]:
            J.append((f'rec_s{s}_g{gx}_single',s,gx,BGW,0.15,0,'single'))
            for nm,k in [('rip12','rip:0123:12:1'),('rip16','rip:0123:16:1'),('rip20','rip:0123:20:1'),('sh16','rip:2031:16:1')]:
                J.append((f'rec_s{s}_g{gx}_{nm}',s,gx,BGW,0.15,0,k))
            J.append((f'rec_s{s}_g{gx}_rip12_SG',s,gx,BGW,0.15,1,'rip:0123:12:1'))
    if r=='R3':  # uniform background: weight 1.0, per-pair conductance = min(g, c)
        for c in [0.15,0.2,0.3,0.4,0.5,0.75,1.0]:
            J.append((f'u_c{c}_SG',1,1,1.0,c,1,'rip:0123:12:1'))
            for s,gx in [(1,1),(3,5),(5,5),(7,5),(10,5),(10,10)]:
                J.append((f'u_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'rip:0123:12:1'))
    if r=='R8':  # overlap, S1, single runs (4-cell + 3-cell cues)
        for k in (0,1,2,3):
            for c in (0.15,0.3,0.45):
                J.append((f'ovl_k{k}_c{c}_SG',1,1,1.0,c,1,'single'))
                for s,gx in [(1,1),(3,5),(5,5)]:
                    J.append((f'ovl_k{k}_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'single'))
    if r=='R9':  # overlap on seed 629
        for k in (0,2,3):
            for c in (0.15,0.45):
                J.append((f's629_ovl_k{k}_c{c}_SG',1,1,1.0,c,1,'single'))
                for s,gx in [(1,1),(3,5),(5,5)]:
                    J.append((f's629_ovl_k{k}_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'single'))
    if r=='R6':  # S1 fine threshold scan + x20/x10 extension points
        for c in [0.45,0.55,0.6,0.65,0.7,0.8,0.85,0.9]:
            J.append((f'u_c{c}_SG',1,1,1.0,c,1,'rip:0123:12:1'))
            for s,gx in [(1,1),(3,5),(5,5),(7,5)]:
                J.append((f'u_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'rip:0123:12:1'))
        for c in (0.15,0.75):
            J.append((f'u_c{c}_s20_g10',20,10,1.0,c,0,'rip:0123:12:1'))
    if r=='R7':  # seed 629 fine threshold
        for c in [0.55,0.6,0.65,0.7,0.8,0.9]:
            J.append((f's629_u_c{c}_SG',1,1,1.0,c,1,'rip:0123:12:1'))
            for s,gx in [(1,1),(3,5),(5,5),(7,5)]:
                J.append((f's629_u_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'rip:0123:12:1'))
    if r in ('R4','R5'):  # second seed network 629: uniform background; R5 = recall (single c0.15 + 3-cell) and ripples at c0.15
        if r=='R4':
            for c in [0.15,0.5,0.75,1.0,1.5]:
                J.append((f's629_u_c{c}_SG',1,1,1.0,c,1,'rip:0123:12:1'))
                for s,gx in [(1,1),(3,5),(5,5),(7,5)]:
                    J.append((f's629_u_c{c}_s{s}_g{gx}',s,gx,1.0,c,0,'rip:0123:12:1'))
        else:
            for s,gx in [(1,1),(3,5),(5,5),(7,5)]:
                J.append((f's629_rec_s{s}_g{gx}_single',s,gx,1.0,0.15,0,'single'))
                for nm,k in [('rip16','rip:0123:16:1'),('rip20','rip:0123:20:1'),('sh16','rip:2031:16:1')]:
                    J.append((f's629_rec_s{s}_g{gx}_{nm}',s,gx,1.0,0.15,0,k))
    return J
def runone(j):
    tag,s,gx,bgw,c,sg,kind=j; SD='629' if tag.startswith('s629') else None; model=patch_B.name(s,gx,SD)
    cmd=[PY,H+'runB.py',tag,model,str(s),str(gx),str(bgw),str(c),str(sg),kind]
    env=dict(os.environ); 
    if tag.startswith('ovl_'): env['OVL']=H+'groups_ovl_k%s.json'%tag.split('_')[1][1:]
    if tag.startswith('s629_ovl_'): env['OVL']=H+'groups_ovl629_k%s.json'%tag.split('_')[2][1:]
    
    if SD: env['SEED']=SD
    out=subprocess.run(cmd,capture_output=True,text=True,cwd=H,env=env)
    txt=(out.stdout+out.stderr).replace('\r','\n'); lines=[l for l in txt.split('\n') if l.strip() and not any(x in l for x in ('Waiting','Warn','_color','AuthKey'))]
    open(H+'log_%s.txt'%tag,'w').write('\n'.join(lines)); return tag,out.returncode
if __name__=='__main__':
    J=rounds(sys.argv[1]); conds=sorted({(j[1],j[2]) for j in J}); made=[]
    try:
        for s,gx in conds:
            sd='629' if sys.argv[1] in ('R4','R5','R7','R9') else None
            nm=patch_B.name(s,gx,sd)
            if not os.path.exists(patch_B.D+nm): patch_B.make(s,gx,patch_B.SEEDS[sd] if sd else 'v2-arbor-S10000',nm); made.append(nm)
        J=[j for j in J if not os.path.exists(H+'raw_%s.json'%j[0])]
        with ThreadPoolExecutor(2) as ex:
            for t,rc in ex.map(runone,J): print(t,rc,flush=True)
    finally:
        for m in made: patch_B.delete(m)
    print('done')
