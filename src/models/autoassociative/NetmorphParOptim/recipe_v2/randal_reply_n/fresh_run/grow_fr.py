#!/usr/bin/env python3
"""Line-379-fix driver (copy of pv_arbor_seeds/grow_pv.py; talks to the patched instance on API port 8010). usage: grow_pv.py S1|V1|V3 SEED (one run per process)."""
import os, subprocess, sys, time
W = '/home/johnjose/cos/netmorph_work'; HERE = W + '/recipe_v2/randal_reply_n/fresh_run'
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
def ax2(b,E=0.319251): return ['all_interneuron_axons.branching_model=van_Pelt;', 'all_interneuron_axons.B_inf=%g;' % b, 'all_interneuron_axons.tau=1681541;', 'all_interneuron_axons.E=%g;' % E, 'all_interneuron_axons.E_competes_with=same_arbor;', 'all_interneuron_axons.min_node_interval=0.0;']
CFG = {'S1': (B610 + dn(3.5) + ax2(26), 0, 48), 'V1': (B610 + dn(3.5) + ax2(20), 0, 48), 'V3': (B610 + dn(5) + ax2(23), 0, 48), 'V1n30': (B610 + dn(3.5) + ax2(20), 0, 30), 'S1n30': (B610 + dn(3.5) + ax2(26), 0, 30), 'V3n30': (B610 + dn(5) + ax2(23), 0, 30), 'V3n24': (B610 + dn(5) + ax2(23), 0, 24), 'V3n20': (B610 + dn(5) + ax2(23), 0, 20), 'V1n24': (B610 + dn(3.5) + ax2(20), 0, 24), 'V1n20': (B610 + dn(3.5) + ax2(20), 0, 20)}
ARM = sys.argv[1]; seed = int(sys.argv[2]); name = 'V1n20'; extra, _, NI = CFG[name]
# arm: (interneuron-axon own dm weight or None, steering, pyramidal D_synmax)
ARMS = {'A0': (0.9, False, 0.0175), 'A1': (0.3, False, 0.0175), 'A2': (0.6, False, 0.0175), 'A3': (1.0, False, 0.0175), 'A4': (0.6, True, 0.0175), 'A5': (1.0, True, 0.0175), 'B1': (None, False, 0.035), 'B2': (None, False, 0.05), 'C1': (None, 'GRP', 0.0175)}
WI, STEER, DPP = ARMS[ARM]; DI = 0.03
tag = '%s_s%d' % (ARM, seed)
if WI is not None:
    assert 0.1 <= WI <= 1.0
    extra = extra + ['all_interneuron_axons.direction_model=segment_history_tension;', 'all_interneuron_axons.dm_label=axondm;', 'all_interneuron_axons.axondm.dm_weight=%g;' % WI, 'all_interneuron_axons.axondm.direction_model=cell_attraction;']
STEER_LINES = []
if STEER:   # C1: 8 groups of 6 pyramidal cells (indices 6g..6g+5, first 48 cells); own-group dendrites only for grouped cells
    for k in range(96):
        if k < 48: g = k // 6; STEER_LINES += ['idx.In.pyramidal.%d.attractors=NGF_A NGF_G%d;' % (k, g), 'idx.In.pyramidal.%d.attractedto=NGF_G%d;' % (k, g)]
        else: STEER_LINES += ['idx.In.pyramidal.%d.attractors=NGF_A;' % k, 'idx.In.pyramidal.%d.attractedto=NGF_A;' % k]
    for j in range(NI): STEER_LINES += ['idx.In.interneuron.%d.attractors=NGF_A;' % j, 'idx.In.interneuron.%d.attractedto=NGF_A;' % j]
    extra = extra + STEER_LINES
VALS[2] = NI
df = pd.DataFrame([dict(zip(F, map(float, VALS)))]); bio_check.assert_hard_limits(df)
rd = '%s/grow_%s' % (HERE, tag); os.makedirs(rd, exist_ok=True)
base = open(N + '/nesvbp-autoassociative').read(); assert 'D_synmax' not in base
if STEER:
    assert base.count('In.attractedto=NGF_A;') == 1 and base.count('In.attractors=NGF_A;') == 1
    base = base.replace('\nIn.attractedto=NGF_A;', '\n#In.attractedto=NGF_A; (replaced by per-cell lines, randal_reply_n)').replace('\nIn.attractors=NGF_A;', '\n#In.attractors=NGF_A; (replaced by per-cell lines)')
mf = rd + '/model_' + tag
open(mf, 'w').write(base + '\nD_synmax.pyramidal.pyramidal=%g;\nD_synmax.pyramidal.interneuron=%g;\nD_synmax.interneuron.pyramidal=%g;\nD_synmax.interneuron.interneuron=%g;\n' % (DPP, DI, DI, DI) + ''.join(x + '\n' for x in extra))
wb = openpyxl.Workbook(); ws = wb.active; ws.append(F); ws.append([int(v) if f != 'dm.weight' else float(v) for f, v in zip(F, VALS)]); wb.save(rd + '/s.xlsx')
t = time.time()
cmd = [PY, N + '/gen_autonm_labels.py', '-excel', rd + '/s.xlsx', '-out', rd + '/out.xlsx', '-modelfile', mf, '-modelname', 'v2-fr-' + tag, '-savemodels',
       '-deleteresident', '-batchlimit', '1', '-vizdir', rd + '/viz', '-randomseed', str(seed), '-Port', '8010']
with open(rd + '/run.log', 'w') as lg:
    p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONPATH='/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:' + W + '/extra'))
    p.stdin.write(b'n\n'); p.stdin.close()
    try: rc = p.wait(timeout=None)
    except subprocess.TimeoutExpired: p.terminate(); rc = 'TIMEOUT'
open(rd + '/result.txt', 'w').write('config %s seed=%d rc=%s wall=%d\n' % (tag, seed, rc, time.time() - t))
print(tag, 'rc', rc, 'wall', int(time.time() - t), flush=True)
