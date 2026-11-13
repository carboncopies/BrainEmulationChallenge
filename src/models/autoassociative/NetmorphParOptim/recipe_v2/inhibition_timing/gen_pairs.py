"""Export R3 pair lists (as fable_design_S1/design.export_pairs) for the redesigned groups. usage: gen_pairs.py TAG (reads groups_TAG.json)"""
import sys, json
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
tag=sys.argv[1]; g=[(sorted(x['members']),sorted(x['cue'])) for x in json.load(open('groups_%s.json'%tag))['groups']]
for c in ('0','0.15','0.25','0.5'):
    kw=dict(T=16.5,Lnn=8,Lnc=8)
    if c!='0': kw.update(bg=0.2,pc=float(c))
    export_pairs(g,'pairs_%s_c%s.json'%(tag,c),**kw)
print('ok',tag)
