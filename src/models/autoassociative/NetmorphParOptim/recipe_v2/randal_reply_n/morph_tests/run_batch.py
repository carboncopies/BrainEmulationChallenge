#!/usr/bin/env python3
"""Grow one batch (one samples sheet, several rows grown in parallel) on morph_tests instance k with the generator copy.
usage: run_batch.py K [--rows all]   K selects the instance (ports 8100+10K) and the rows: seed SEEDS[K//2], arms HALVES[K%2].
The samples sheet (batch_i<K>/samples.xlsx) has Randal's 7 columns plus 'arm', 'randomseed' and 'nm.<directive>' columns
(read only by gen_autonm_labels_mt.py; the original generator ignores them)."""
import os, subprocess, sys, time, json
H = os.path.dirname(os.path.abspath(__file__))
BEC = '/home/johnjose/BrainGenix/wt/bec-netmorph/src'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim');sys.path.insert(0, '/home/johnjose/cos/netmorph_work/extra')
import pandas as pd, bio_check, openpyxl
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
E4 = [25, 96, 20, 10, 120, 30, 0.9]
ARMS = {  # arm: (dm.weight, {directive: value})
    'A09': (0.9, {}), 'A05': (0.5, {}), 'A02': (0.2, {}), 'A01': (0.1, {}),
    'Bs': (0.9, {'detailed_chemical_factors': 'false', 'soma_attraction_weight': '1.0'}),
    'Bsd': (0.9, {'soma_attraction_weight': '1.0'}),
}
SEEDS = [66666, 77777, 88888, 99999]
HALVES = [['A09', 'A05', 'A02'], ['A01', 'Bs', 'Bsd']]
NMCOLS = ['nm.detailed_chemical_factors', 'nm.soma_attraction_weight']

def rows_for(k):
    seed = SEEDS[k // 2]; out = []
    for arm in HALVES[k % 2]:
        dm, ex = ARMS[arm]; v = E4[:6] + [dm]
        r = dict(zip(F, v)); r.update(arm=arm, randomseed=seed); r.update({c: ex.get(c[3:], '') for c in NMCOLS}); out.append(r)
    return out

def write_sheet(rows, path):
    cols = F + ['arm', 'randomseed'] + NMCOLS
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(cols)
    for r in rows: ws.append([(int(r[c]) if c in F[:6] else r[c]) for c in cols])
    wb.save(path)

if __name__ == '__main__':
    k = int(sys.argv[1]); port = 8100 + 10 * k
    rows = rows_for(k)
    df = pd.DataFrame([{f: float(r[f]) for f in F} for r in rows]); bio_check.assert_hard_limits(df)
    rd = '%s/batch_i%d' % (H, k); os.makedirs(rd, exist_ok=True)
    write_sheet(rows, rd + '/samples.xlsx')
    t = time.time()
    cmd = [PY, H + '/gen_autonm_labels_mt.py', '-excel', rd + '/samples.xlsx', '-out', rd + '/out.xlsx', '-modelfile', H + '/model_E4',
           '-modelname', 'mt-i%d-' % k, '-deleteresident', '-batchlimit', '3', '-vizdir', rd + '/viz', '-Port', str(port)]
    env = dict(os.environ, PYTHONPATH=':'.join(['/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient', BEC + '/models/autoassociative', BEC + '/components', '/home/johnjose/cos/netmorph_work/extra']),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    json.dump(dict(k=k, port=port, rows=rows, cmd=cmd, start=time.strftime('%F %T')), open(rd + '/launch.json', 'w'), indent=1)
    with open(rd + '/run.log', 'w') as lg:
        p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=env)
        p.stdin.write(b'n\n'); p.stdin.close(); rc = p.wait()
    open(rd + '/result.txt', 'w').write('instance %d rc=%s wall=%d end=%s\n' % (k, rc, time.time() - t, time.strftime('%F %T')))
    print('i%d rc %s wall %d' % (k, rc, time.time() - t), flush=True)
