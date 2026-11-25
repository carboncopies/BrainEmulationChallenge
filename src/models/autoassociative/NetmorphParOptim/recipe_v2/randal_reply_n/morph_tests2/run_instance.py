#!/usr/bin/env python3
"""Run all sub-batches assigned to morph_tests2 instance K (sequentially), restarting the instance between sub-batches if NES RSS > 10 GB,
and starting nothing new while STOP_NEW exists.  usage: run_instance.py K
Rows: Randal's 7 sheet columns + arm, size, randomseed (read only by gen_autonm_labels_mt2.py)."""
import os, subprocess, sys, time, json
H = os.path.dirname(os.path.abspath(__file__))
BEC = '/home/johnjose/BrainGenix/wt/bec-netmorph/src'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/extra'); sys.path.insert(0, H + '/bio')                      # COPY of bio_check + bio_ranges.json (pyramidal max 300)
import pandas as pd, bio_check, openpyxl
assert os.path.dirname(os.path.abspath(bio_check.__file__)) == H + '/bio'
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
SIZES = {'x1': (96, 20, 120, 30), 'x1.5': (144, 30, 147, 30), 'x2': (192, 40, 170, 30), 'x3': (288, 60, 200, 32), 'ctrl': (96, 20, 170, 30)}
SEEDS = [66666, 77777, 88888]
DMS = [0.9, 0.1, 0.2]

def row(size, dm, seed):
    P, I, R, T = SIZES[size]
    return {'days': 25, 'pyramidal': P, 'interneuron': I, 'minneuronseparation': 10, 'shape.radius': R, 'shape.thickness': T, 'dm.weight': dm,
            'arm': '%s_dm%02d' % (size, round(dm * 10)), 'size': size, 'randomseed': seed}

def plan(k):
    seed = SEEDS[k // 3]; r = k % 3
    if r == 0: return [[row('x3', d, seed) for d in DMS]]
    if r == 1: return [[row('x2', d, seed) for d in DMS]]
    return [[row('x1.5', d, seed) for d in DMS], [row('x1', d, seed) for d in DMS] + [row('ctrl', 0.1, seed)]]

def nes_rss_kb(k):
    try:
        p = open('%s/instances/i%d/nes.pid' % (H, k)).read().strip()
        return int([l.split()[1] for l in open('/proc/%s/status' % p) if l.startswith('VmRSS')][0])
    except Exception: return -1

def log(k, msg):
    open('%s/instance_events.log' % H, 'a').write('%s i%d %s\n' % (time.strftime('%F %T'), k, msg))

if __name__ == '__main__':
    k = int(sys.argv[1]); port = 8200 + 10 * k
    for b, rows in enumerate(plan(k)):
        while os.path.exists(H + '/STOP_NEW'): log(k, 'STOP_NEW present, waiting'); time.sleep(120)
        rss = nes_rss_kb(k)
        if b > 0 and rss > 10 * 1048576:
            log(k, 'NES RSS %d kB > 10 GB before sub-batch %d: restart' % (rss, b))
            subprocess.run([H + '/inst.sh', 'stop', str(k)]); time.sleep(10); subprocess.run([H + '/inst.sh', 'start', str(k)])
        df = pd.DataFrame([{f: float(r[f]) for f in F} for r in rows]); bio_check.assert_hard_limits(df)
        rd = '%s/batch_i%d_b%d' % (H, k, b); os.makedirs(rd, exist_ok=True)
        cols = F + ['arm', 'size', 'randomseed']
        wb = openpyxl.Workbook(); ws = wb.active; ws.append(cols)
        for r in rows: ws.append([r[c] for c in cols])
        wb.save(rd + '/samples.xlsx')
        cmd = [PY, H + '/gen_autonm_labels_mt2.py', '-excel', rd + '/samples.xlsx', '-out', rd + '/out.xlsx', '-modelfile', H + '/model_E4',
               '-modelname', 'mt2-i%d-b%d-' % (k, b), '-deleteresident', '-batchlimit', '3', '-vizdir', rd + '/viz', '-Port', str(port)]
        env = dict(os.environ, PYTHONPATH=':'.join(['/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient', BEC + '/models/autoassociative', BEC + '/components', '/home/johnjose/cos/netmorph_work/extra']),
                   OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        t = time.time(); json.dump(dict(k=k, b=b, port=port, rows=rows, cmd=cmd, start=time.strftime('%F %T'), nes_rss_kb_before=rss), open(rd + '/launch.json', 'w'), indent=1)
        log(k, 'start sub-batch %d: %s' % (b, ' '.join(r['arm'] for r in rows)))
        with open(rd + '/run.log', 'w') as lg:
            p = subprocess.Popen(cmd, cwd=rd, stdin=subprocess.PIPE, stdout=lg, stderr=subprocess.STDOUT, env=env)
            p.stdin.write(b'n\n'); p.stdin.close(); rc = p.wait()
        open(rd + '/result.txt', 'w').write('instance %d sub-batch %d rc=%s wall=%d end=%s nes_rss_kb_after=%d\n' % (k, b, rc, time.time() - t, time.strftime('%F %T'), nes_rss_kb(k)))
        log(k, 'end sub-batch %d rc=%s wall=%d rss_after=%d' % (b, rc, time.time() - t, nes_rss_kb(k)))
    open('%s/instance_i%d.done' % (H, k), 'w').write(time.strftime('%F %T') + '\n')
