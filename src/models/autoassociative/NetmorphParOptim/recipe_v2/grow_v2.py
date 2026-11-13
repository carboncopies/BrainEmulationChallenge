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
CFG = {  # name: (values for F, D_synmax interneuron pairs, description)
 'a': ([25, 96, 48, 10, 120, 30, 0.9], 0.1, "Randal's 96/48"),
 'b': ([25, 70, 30, 12, 113, 50, 1.0], 0.1, 'h2h scaling-law corner'),
 'c': ([25, 64, 32, 10, 100, 40, 1.0], 0.1, 'smaller volume, denser'),
 'd': ([25, 70, 46, 10, 100, 50, 1.0], 0.1, 'higher interneuron fraction (40%)'),
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
    rd = '%s/grow_%s' % (HERE, name); os.makedirs(rd, exist_ok=True)
    base = open(N + '/nesvbp-autoassociative').read()
    assert 'D_synmax' not in base
    mf = rd + '/model_v2' + name
    open(mf, 'w').write(base + '\nD_synmax.pyramidal.pyramidal=1.5;\nD_synmax.pyramidal.interneuron=%g;\nD_synmax.interneuron.pyramidal=%g;\nD_synmax.interneuron.interneuron=%g;\n' % (di, di, di))
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(F); ws.append([int(v) if f != 'dm.weight' else float(v) for f, v in zip(F, vals)]); wb.save(rd + '/s.xlsx')
    t = time.time()
    cmd = [PY, N + '/gen_autonm_labels.py', '-excel', rd + '/s.xlsx', '-out', rd + '/out.xlsx', '-modelfile', mf, '-modelname', 'v2-' + name, '-savemodels',
           '-deleteresident', '-batchlimit', '1', '-vizdir', rd + '/viz', '-randomseed', '20240628']
    with open(rd + '/run.log', 'w') as lg:
        p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONPATH='/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:' + W + '/extra'))
        p.stdin.write(b'n\n'); p.stdin.close()
        try: rc = p.wait(timeout=1500)
        except subprocess.TimeoutExpired: p.terminate(); rc = 'TIMEOUT'
    open(rd + '/result.txt', 'w').write('config %s %s %s di=%g rc=%s wall=%d\n' % (name, desc, vals, di, rc, time.time() - t))
    print(name, desc, 'rc', rc, 'wall', int(time.time() - t), flush=True)
