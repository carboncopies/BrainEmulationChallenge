#!/usr/bin/env python3
"""Post-hoc: steering indices map to viz ids 48-95 (enrichment found there on both seeds); groups = viz blocks 8..15. Reports the preregistered #3 quantities on those blocks."""
import json,sys,numpy as np
exec(open('c1_metrics.py').read().split("seed = sys.argv")[0])
out={}
for s in (33333,44444):
    S,G=mats(HERE+f'grow_C1_s{s}/viz/sample_0000.json')
    blocks=[list(range(6*g,6*g+6)) for g in range(8,16)]
    m=metrics(S,G,blocks,'C1 steered groups = viz blocks 8-15'); out[s]=m
    print(s,{a:(round(b,3) if isinstance(b,float) else b) for a,b in m.items() if a!='usable'})
    print('  per-group best strong cue-target pairs of 8:',[u['best_strong_cue_target_pairs_of_8'] for u in m['usable']])
    # strong pairs per group size 30 directed
    print('  all-pairs 4+2 feas on C1 whole graph strong pairs',int((G>=4.125).sum()))
json.dump(out,open('c1_metrics_mapped.json','w'),indent=1)
