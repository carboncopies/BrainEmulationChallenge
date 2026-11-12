#!/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
"""Sequential growth driver for the Track-1 head-to-head.
Run with:  PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:/home/johnjose/cos/netmorph_work/extra \
           /home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python run_queue.py queue1.csv [--dry-run]
Queue csv columns: run_id,arm,config_id,days,pyramidal,interneuron,minneuronseparation,shape.radius,shape.thickness,dm.weight,netmorph_seed
Launch = exactly batch B's call (batchB_run.sh): `echo n | gen_autonm_labels.py -excel s.xlsx -out out.xlsx -modelfile nesvbp-autoassociative
-batchlimit 1 -vizdir viz` (+ explicit -randomseed). Base model file has NO D_synmax lines. NEVER passes -deleteresident. One growth at a time."""
import argparse, csv, datetime, json, os, re, signal, subprocess, sys, time
import numpy as np, pandas as pd
from h2h_common import *
PY = '/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python'
N = '/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative'
MODEL = N + '/nesvbp-autoassociative'
LABEL = N + '/gen_autonm_labels.py'
TIMEOUT = 1500; SLEEP = 30
RUNS = H2H + '/runs.csv'
ERR_PAT = re.compile(r'Connection|refused|Max retries|Traceback|NES error|Netmorph error|failed to|Errno', re.I)
LABCOLS = ['raw_pyr_int_n', 'raw_pyr_int_g', 'raw_int_pyr_n', 'raw_int_pyr_g', 'raw_int_int_n', 'raw_int_int_g', 'raw_pyr_pyr_n', 'raw_pyr_pyr_g',
           'usable_conns1', 'usable_conns2', 'usable_pyr_int', 'usable_int_pyr', 'usable_int_int', 'frac_int_driven', 'frac_pyr_inhibited',
           'frac_pyr_inhibited_w05', 'frac_int_ampa_ge13_84', 'n_int_pn', 'mean_gaba_per_pyr_nS']
COLS = ['run_id', 'arm', 'config_id', 'queue', 'timestamp'] + F + ['netmorph_seed', 'NES_SIM_ID', 'wall_s', 'pred_wall_s', 'rc'] + LABCOLS + ['J', 'soft_clean']

def done_ids():
    if not os.path.exists(RUNS): return set()
    r = pd.read_csv(RUNS); return set(r.loc[r['rc'] == 0, 'run_id'])

def append_row(row):
    new = not os.path.exists(RUNS)
    with open(RUNS, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        if new: w.writeheader()
        w.writerow(row)

def assert_row(r):
    df = pd.DataFrame([{f: float(r[f]) for f in F}]); assert_limits(df)
    for f in ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness']:
        assert float(r[f]) == int(round(float(r[f]))), f
    assert abs(float(r['dm.weight']) * 10 - round(float(r['dm.weight']) * 10)) < 1e-9

def write_xlsx(path, r):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(F)
    ws.append([int(r[f]) if f != 'dm.weight' else float(r[f]) for f in F]); wb.save(path)

def cmd_for(rd, seed):
    return [PY, LABEL, '-excel', rd + '/s.xlsx', '-out', rd + '/out.xlsx', '-modelfile', MODEL, '-batchlimit', '1', '-vizdir', rd + '/viz', '-randomseed', str(int(seed))]

def parse_outputs(rd):
    j = json.load(open(rd + '/out-rawcounts.json'))['0']
    if j.get('status') != 'completed': raise RuntimeError('run status %s' % j.get('status'))
    return comps_from_rawcounts(j)

def selftest_parse():
    """Check the component code on a real batch B file: must equal load_batchB()."""
    j = json.load(open(D + 'batchB/out0-rawcounts.json'))['0']; c = comps_from_rawcounts(j)
    b = load_batchB().iloc[0]
    for k in COMP: assert abs(c[k] - b[k]) < 1e-9, k
    return {k: c[k] for k in COMP + ['frac_int_ampa_ge13_84', 'mean_gaba_per_pyr_nS']}

def abort(qname, reason):
    open('%s/%s.status' % (H2H, qname), 'w').write('ABORTED: %s\n' % reason); print('ABORTED:', reason, flush=True); sys.exit(2)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('queue'); ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args()
    qpath = a.queue if os.path.isabs(a.queue) else os.path.join(H2H, a.queue)
    qname = os.path.splitext(os.path.basename(qpath))[0]
    q = pd.read_csv(qpath)
    for _, r in q.iterrows(): assert_row(r)          # generation-time check of the whole queue
    print('queue %s: %d runs; all pass hard limits + size cap' % (qname, len(q)))
    if a.dry_run: print('DRY-RUN parse selftest:', selftest_parse())
    tot_pred = 0.0
    for _, r in q.iterrows():
        pw = float(pred_wall(pd.DataFrame([r])).iloc[0]); tot_pred += pw
        if os.path.exists(H2H + '/STOP'): abort(qname, 'STOP file present') if not a.dry_run else print('STOP present (dry-run)')
        if r['run_id'] in done_ids(): print('SKIP (rc=0 already in runs.csv):', r['run_id']); continue
        assert_row(r)                                  # again immediately before launch
        rd = '%s/runs/%s' % (H2H, r['run_id']); os.makedirs(rd, exist_ok=True)
        write_xlsx(rd + '/s.xlsx', r); cmd = cmd_for(rd, r['netmorph_seed'])
        print('%s %s pred_wall=%.0fs seed=%s\n  cmd: echo n | %s' % (r['run_id'], [r[f] for f in F], pw, r['netmorph_seed'], ' '.join(cmd)), flush=True)
        if a.dry_run: continue
        env = dict(os.environ); t0 = time.time(); rc = None; timed_out = False
        p = subprocess.Popen(cmd, cwd=rd, env=env, stdin=subprocess.PIPE, stdout=open(rd + '/run.log', 'w'), stderr=subprocess.STDOUT, text=True)
        try:
            p.communicate('n\n', timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True; p.send_signal(signal.SIGTERM)          # own client only
            try: p.wait(timeout=60)
            except subprocess.TimeoutExpired: p.kill()
        rc = p.returncode if not timed_out else 124; wall = time.time() - t0
        log = open(rd + '/run.log', errors='replace').read()
        m = re.search(r'NES_SIM_ID=(\S+)', log); sim = m.group(1) if m else ''
        row = {'run_id': r['run_id'], 'arm': r['arm'], 'config_id': r.get('config_id', ''), 'queue': qname, 'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
               'netmorph_seed': int(r['netmorph_seed']), 'NES_SIM_ID': sim, 'wall_s': round(wall, 1), 'pred_wall_s': round(pw, 1), 'rc': rc}
        for f in F: row[f] = r[f]
        reason = None
        if timed_out: reason = 'timeout %ds (%s)' % (TIMEOUT, r['run_id'])
        elif rc != 0: reason = 'non-zero rc=%s (%s)' % (rc, r['run_id'])
        else:
            try:
                c = parse_outputs(rd); row.update(c)
                d = pd.DataFrame([{**{f: float(r[f]) for f in F}, **{k: c[k] for k in COMP}}])
                row['J'] = float(J_of(d)[0]); row['soft_clean'] = bool(soft_clean(d)[0])
            except Exception as e: reason = 'output parse/status error: %s (%s)' % (e, r['run_id']); row['rc'] = 3
            tail = '\n'.join(log.splitlines()[-400:])
            if reason is None and ERR_PAT.search(re.sub(r'\x1b\[[0-9;]*m', '', tail.replace('...checking', ''))) and 'Traceback' in tail:
                reason = 'server/connection error pattern in log (%s)' % r['run_id']; row['rc'] = 4
            if reason is None and wall > 2 * pw: reason = 'wall_s %.0f > 2 x predicted %.0f (%s)' % (wall, pw, r['run_id'])
        append_row(row)
        print('%s rc=%s wall=%.0fs sim=%s J=%s soft_clean=%s' % (r['run_id'], row['rc'], wall, sim, row.get('J'), row.get('soft_clean')), flush=True)
        if reason: abort(qname, reason)
        time.sleep(SLEEP)
    if a.dry_run: print('DRY-RUN done. total predicted wall: %.0f s (%.2f h)' % (tot_pred, tot_pred / 3600)); return
    open('%s/%s.status' % (H2H, qname), 'w').write('DONE\n'); print('DONE')

if __name__ == '__main__': main()
