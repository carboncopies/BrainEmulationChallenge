#!/usr/bin/env python3
"""Axon B_inf rerun driver (copy of grow_v3.py conventions). usage: grow_rerun.py R0|R1|R2|R3  (one run per process; may run concurrently)."""
import os, subprocess, sys, time
W = '/home/johnjose/cos/netmorph_work'; HERE = W + '/recipe_v2/axon_rerun'
sys.path.insert(0, W + '/bec/src/models/autoassociative/NetmorphParOptim'); sys.path.insert(0, W + '/extra')
import pandas as pd, bio_check, openpyxl
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
N = W + '/bec/src/models/autoassociative'
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
VALS = [25, 96, 48, 10, 120, 30, 0.9]
A_L = ['interneuron.min_basal=4;', 'interneuron.max_basal=8;']
def ax(b): return ['all_interneuron_axons.branching_model=van_Pelt;', 'all_interneuron_axons.B_inf=%g;' % b, 'all_interneuron_axons.tau=1681541;', 'all_interneuron_axons.E=0.319251;', 'all_interneuron_axons.E_competes_with=same_arbor;', 'all_interneuron_axons.min_node_interval=0.0;']
CFG = {'R0': (A_L, 20240628), 'R1': (A_L + ax(26), 20240628), 'R2': (A_L + ax(39), 20240628), 'R3': (A_L, 20240629)}
name = sys.argv[1]; extra, seed = CFG[name]
df = pd.DataFrame([dict(zip(F, map(float, VALS)))]); bio_check.assert_hard_limits(df)
rd = '%s/grow_%s' % (HERE, name); os.makedirs(rd, exist_ok=True)
base = open(N + '/nesvbp-autoassociative').read(); assert 'D_synmax' not in base
mf = rd + '/model_' + name
open(mf, 'w').write(base + '\nD_synmax.pyramidal.pyramidal=1.5;\nD_synmax.pyramidal.interneuron=0.1;\nD_synmax.interneuron.pyramidal=0.1;\nD_synmax.interneuron.interneuron=0.1;\n' + ''.join(x + '\n' for x in extra))
wb = openpyxl.Workbook(); ws = wb.active; ws.append(F); ws.append([int(v) if f != 'dm.weight' else float(v) for f, v in zip(F, VALS)]); wb.save(rd + '/s.xlsx')
t = time.time()
cmd = [PY, N + '/gen_autonm_labels.py', '-excel', rd + '/s.xlsx', '-out', rd + '/out.xlsx', '-modelfile', mf, '-modelname', 'v2-arbor-' + name, '-savemodels',
       '-deleteresident', '-batchlimit', '1', '-vizdir', rd + '/viz', '-randomseed', str(seed)]
with open(rd + '/run.log', 'w') as lg:
    p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONPATH='/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:' + W + '/extra'))
    p.stdin.write(b'n\n'); p.stdin.close()
    try: rc = p.wait(timeout=3600)
    except subprocess.TimeoutExpired: p.terminate(); rc = 'TIMEOUT'
open(rd + '/result.txt', 'w').write('config %s seed=%d rc=%s wall=%d\n' % (name, seed, rc, time.time() - t))
print(name, 'rc', rc, 'wall', int(time.time() - t), flush=True)
