#!/usr/bin/env python3
"""Axon B_inf rerun driver (copy of grow_v3.py conventions). usage: grow_seed.py S1-seed629|S1-seed630 (same as dendrite_rerun/grow_dend.py S1, only seed differs)  (one run per process; may run concurrently)."""
import os, subprocess, sys, time
W = '/home/johnjose/cos/netmorph_work'; HERE = W + '/recipe_v2/robustness_S1'
sys.path.insert(0, W + '/bec/src/models/autoassociative/NetmorphParOptim'); sys.path.insert(0, W + '/extra')
import pandas as pd, bio_check, openpyxl
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
N = W + '/bec/src/models/autoassociative'
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
VALS = [25, 96, 48, 10, 120, 30, 0.9]
A_L = ['interneuron.min_basal=4;', 'interneuron.max_basal=8;']
def ax(b): return ['all_interneuron_axons.branching_model=van_Pelt;', 'all_interneuron_axons.B_inf=%g;' % b, 'all_interneuron_axons.tau=1681541;', 'all_interneuron_axons.E=0.319251;', 'all_interneuron_axons.E_competes_with=same_arbor;', 'all_interneuron_axons.min_node_interval=0.0;']
def dn(b): return ['all_interneuron_dendrites.branching_model=van_Pelt;', 'all_interneuron_dendrites.B_inf=%g;' % b, 'all_interneuron_dendrites.tau=259680;', 'all_interneuron_dendrites.E=0.73;', 'all_interneuron_dendrites.E_competes_with=same_arbor;', 'all_interneuron_dendrites.min_node_interval=2.0;']
B610 = ['interneuron.min_basal=6;', 'interneuron.max_basal=10;']
CFG = {'S1-seed629': (B610 + dn(3.5) + ax(26), 20240629, 48), 'S1-seed630': (B610 + dn(3.5) + ax(26), 20240630, 48)}
name = sys.argv[1]; extra, seed, NI = CFG[name]
VALS[2] = NI
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
    try: rc = p.wait(timeout=None)
    except subprocess.TimeoutExpired: p.terminate(); rc = 'TIMEOUT'
open(rd + '/result.txt', 'w').write('config %s seed=%d rc=%s wall=%d\n' % (name, seed, rc, time.time() - t))
print(name, 'rc', rc, 'wall', int(time.time() - t), flush=True)
