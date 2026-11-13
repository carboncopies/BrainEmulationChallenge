import json, sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
import ripple_lib as R
from ripple_lib import *
D = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/'
cond = {(a, b): c for a, b, c, g in PAIRS}
allm = {m for mem, _ in GROUPS for m in mem}
rows = []
for i in dump.its:
    drive = sum(cond.get((m, i), 0.0) for m in allm)
    back = {str(m): round(float(dump.GA[i, m]), 2) for m in allm if dump.GA[i, m] > 0}
    rows.append((drive + sum(back.values()) * 0, i, drive, back))
# strongest: rank by programmed drive from memory members, require projection back
rows = [r for r in rows if r[2] > 0 and r[3]]
rows.sort(key=lambda r: -r[2])
INTS = [dict(id=i, drive_from_all_memory_members_nS=round(d, 2), n_members_inhibited=len(b), total_gaba_to_members_nS=round(sum(b.values()), 2), gaba_g_to_members_nS=b) for _, i, d, b in rows[:8]]
ung = [i for i in dump.pyr if i not in allm]
by = sorted(((sum(float(dump.G[m, u]) for m in allm), u) for u in ung), reverse=True)[:3]
BY = [dict(id=u, asgrown_input_from_members_nS=round(s, 2)) for s, u in by]
MEMN = []
for gi, (mem, cue) in enumerate(GROUPS):
    nc = [m for m in mem if m not in cue]
    MEMN += [(cue[0], gi, 'cue cell'), (nc[0], gi, 'non-cue member'), (nc[1], gi, 'non-cue member')]
roles = [(m, 'pyramidal', 'G%d %s' % (g, r)) for m, g, r in MEMN] + [(i['id'], 'interneuron', 'interneuron') for i in INTS] + [(b['id'], 'pyramidal', 'bystander') for b in BY]
print(INTS, BY, flush=True)
NES, client = L.connect()
cases = [('fail_sep16_order0123', [(g, g * 16) for g in range(K)]), ('best_sep16_shuffled_2_0_3_1', [(g, i * 16) for i, g in enumerate([2, 0, 3, 1])])]
out = dict(label='sensitivity study, D_synmax 0.5, not bio-realistic', window_ms=[-5, 110], cue_offsets_ms=CUE_OFFS, neurons=[dict(id=n, type=t, role=r) for n, t, r in roles], interneuron_selection=INTS, bystander_selection=BY, cases={})
first = True
for name, ev in cases:
    for dt in (0.1, 1.0):
        if not first: time.sleep(30)
        first = False
        r, rec = run_case(NES, client, '%s_dt%g' % (name, dt), ev, program=True, run_ms=112.0, dt=dt, record=True)
        t = np.array(rec['t_ms'], float) - T0; msk = (t >= -5) & (t <= 110.0)
        tr = {}
        for nid, typ, role in roles:
            e = rec['neurons'][str(nid)]; vm = np.array(e['Vm_mV'] if isinstance(e, dict) else e, float)
            tr[str(nid)] = [round(float(x), 1) for x in vm[msk]]
        out['cases'].setdefault(name, {'events': ev, 'cues': r['cues']})['dt%g' % dt] = dict(times_ms=[round(float(x), 2) for x in t[msk]], vm_mV=tr, spikes_all_neurons=({str(k): v for k, v in r['spikes'].items() if v}))
        print(name, dt, 'samples', int(msk.sum()), flush=True)
json.dump(out, open(D + 'ripple_vm_full.json', 'w'), separators=(',', ':'))
