#!/usr/bin/env python3
"""Phase 1 growth driver. usage: grow_v2.py name [name...]   (one growth at a time, 30 s pause, memory guard >=100 GB)
Directives: D_synmax.pyramidal.pyramidal=1.5 and the three interneuron pairs = DI (0.1 or 0.15), appended to the base model file.
Hard limits asserted with bio_check before every growth. Model saved by gen_autonm_labels (-savemodels) as v2-<name>0000; sim deleted afterwards (-deleteresident)."""
import json, os, subprocess, sys, time
W = '/home/johnjose/cos/netmorph_work'; HERE = W + '/recipe_v2'
sys.path.insert(0, W + '/bec/src/models/autoassociative/NetmorphParOptim'); sys.path.insert(0, W + '/extra')
import pandas as pd, bio_check
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
N = W + '/bec/src/models/autoassociative'
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
A_L=['interneuron.min_basal=4;','interneuron.max_basal=8;']
B_L=['all_interneuron_axons.branching_model=van_Pelt;','all_interneuron_axons.B_inf=13.21658;','all_interneuron_axons.tau=864000;','all_interneuron_axons.E=0.319251;','all_interneuron_axons.E_competes_with=same_arbor;','all_interneuron_axons.min_node_interval=2.0;']
D_L=['interneuron.min_basal=6;','interneuron.max_basal=8;','all_interneuron_dendrites.branching_model=van_Pelt;','all_interneuron_dendrites.B_inf=3.5;','all_interneuron_dendrites.tau=259680;','all_interneuron_dendrites.E=0.73;','all_interneuron_dendrites.E_competes_with=same_arbor;','all_interneuron_dendrites.min_node_interval=2.0;',
 'all_interneuron_axons.branching_model=van_Pelt;','all_interneuron_axons.B_inf=13.21658;','all_interneuron_axons.tau=432000;','all_interneuron_axons.E=0.319251;','all_interneuron_axons.E_competes_with=same_arbor;','all_interneuron_axons.min_node_interval=2.0;']
EXTRA={'A':A_L,'B':B_L,'C':A_L+B_L,'D':D_L}
CAP=3600
BASE=[25, 96, 48, 10, 120, 30, 0.9]
CFG = {  # name: (values for F, D_synmax interneuron pairs, description)
 'a': ([25, 96, 48, 10, 120, 30, 0.9], 0.1, "Randal's 96/48"),
 'b': ([25, 70, 30, 12, 113, 50, 1.0], 0.1, 'h2h scaling-law corner'),
 'c': ([25, 64, 32, 10, 100, 40, 1.0], 0.1, 'smaller volume, denser'),
 'd': ([25, 70, 46, 10, 100, 50, 1.0], 0.1, 'higher interneuron fraction (40%)'),
 'A': (BASE, 0.1, 'arbor A dendrites'), 'B': (BASE, 0.1, 'arbor B axons'), 'C': (BASE, 0.1, 'arbor C both moderate'), 'D': (BASE, 0.1, 'arbor D both strong'),
 'e': ([25, 96, 48, 10, 120, 30, 0.9], 0.15, "Randal's 96/48 with interneuron D_synmax 0.15"),
}
def mem_gb():
    for l in open('/proc/meminfo'):
        if l.startswith('MemAvailable'): return int(l.split()[1]) / 1048576
for k, name in enumerate(sys.argv[1:]):
    vals, di, desc = CFG[name]
    df = pd.DataFrame([dict(zip(F, map(float, vals)))]); bio_check.assert_hard_limits(df)
    m = mem_gb(); assert m >= 100, 'available memory %.1f GB < 100 GB: stop' % m
    if k: time.sleep(30)
    rd = '%s/grow_arbor_%s' % (HERE, name); os.makedirs(rd, exist_ok=True)
    base = open(N + '/nesvbp-autoassociative').read()
    assert 'D_synmax' not in base
    mf = rd + '/model_v2' + name
    open(mf, 'w').write(base + '\nD_synmax.pyramidal.pyramidal=1.5;\nD_synmax.pyramidal.interneuron=%g;\nD_synmax.interneuron.pyramidal=%g;\nD_synmax.interneuron.interneuron=%g;\n' % (di, di, di) + ''.join(x + '\n' for x in EXTRA.get(name, [])))
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(F); ws.append([int(v) if f != 'dm.weight' else float(v) for f, v in zip(F, vals)]); wb.save(rd + '/s.xlsx')
    t = time.time()
    cmd = [PY, N + '/gen_autonm_labels.py', '-excel', rd + '/s.xlsx', '-out', rd + '/out.xlsx', '-modelfile', mf, '-modelname', 'v2-arbor-' + name, '-savemodels',
           '-deleteresident', '-batchlimit', '1', '-vizdir', rd + '/viz', '-randomseed', '20240628']
    with open(rd + '/run.log', 'w') as lg:
        p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONPATH='/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:' + W + '/extra'))
        p.stdin.write(b'n\n'); p.stdin.close()
        try: rc = p.wait(timeout=CAP)
        except subprocess.TimeoutExpired: p.terminate(); rc = 'TIMEOUT'
    open(rd + '/result.txt', 'w').write('config %s %s %s di=%g rc=%s wall=%d\n' % (name, desc, vals, di, rc, time.time() - t))
    print(name, desc, 'rc', rc, 'wall', int(time.time() - t), flush=True)
