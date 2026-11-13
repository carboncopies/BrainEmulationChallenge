"""usage: run_r3.py NAME PAIRS SG(0|1) KIND   KIND: single | rip:order:spacing:dt[:cue3grp][:rec]   -> raw_NAME.json"""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
from r3lib import *
name, pname, sg, kind = sys.argv[1], sys.argv[2], sys.argv[3] == '1', sys.argv[4]
NES, client = L.connect()
p = kind.split(':')
if p[0] == 'single': e = single_run(NES, client, name, pname, sg)
else:
    rec = 'rec' in p[1:]; q = [x for x in p if x != 'rec']
    e = ripple_run(NES, client, name, pname, sg, [int(c) for c in q[1]], float(q[2]), float(q[3]), cue3=(int(q[4]) if len(q) > 4 else None), record=rec)
e.update(name=name, pairs=pname, sg=sg)
json.dump(e, open(OUT + 'raw_%s.json' % name, 'w'), separators=(',', ':'))
