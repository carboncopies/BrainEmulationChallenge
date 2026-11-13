"""usage: run_vm_mech.py EXPNAME(E1|E2|E3|E4|E4b_alternative) case_name[:label] ... ; Vm at Dt 0.1 ms, -5..+110 ms. sensitivity study, D_synmax 0.5, not bio-realistic"""
import sys, json, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
import mech_lib as M
from mech_lib import *
name = sys.argv[1]; cases = sys.argv[2:]
groups, ref, plist, info = build_set(name)
raw = json.load(open(D + 'raw_mech_%s.json' % name.split('_')[0]))
cond = {(a, b): c for a, b, c, g in plist}
allm = {m for mem, _ in groups for m in mem}
rows = []
for i in dump.its:
    drive = sum(cond.get((m, i), 0.0) for m in allm); back = {str(m): round(float(dump.GA[i, m]), 2) for m in allm if dump.GA[i, m] > 0}
    if drive > 0 and back: rows.append((drive, i, back))
rows.sort(key=lambda r: -r[0])
INTS = [dict(id=i, drive_from_all_memory_members_nS=round(d, 2), n_members_inhibited=len(b), total_gaba_to_members_nS=round(sum(b.values()), 2), gaba_g_to_members_nS=b) for d, i, b in rows[:8]]
ung = [i for i in dump.pyr if i not in allm]
by = sorted(((sum(float(dump.G[m, u]) for m in allm), u) for u in ung), reverse=True)[:3]
BY = [dict(id=u, asgrown_input_from_members_nS=round(s, 2)) for s, u in by]
roles = []
for gi, (mem, cue) in enumerate(groups):
    nc = [m for m in mem if m not in cue]
    roles += [(cue[0], 'pyramidal', 'G%d cue cell' % gi), (nc[0], 'pyramidal', 'G%d non-cue member' % gi), (nc[1], 'pyramidal', 'G%d non-cue member' % gi)]
roles += [(i['id'], 'interneuron', 'interneuron') for i in INTS] + [(b['id'], 'pyramidal', 'bystander') for b in BY]
NES, client = L.connect()
out = dict(label='sensitivity study, D_synmax 0.5, not bio-realistic', experiment=name, window_ms=[-5, 110], dt_ms=0.1, cue_offsets_ms=CUE_OFFS,
           neurons=[dict(id=n, type=t, role=r) for n, t, r in roles], interneuron_selection=INTS, bystander_selection=BY, cases={})
first = True
for c in cases:
    cname, _, lab = c.partition(':')
    ev = raw['runs'][cname]['events']; ev = [tuple(e) for e in ev]
    if not first: time.sleep(30)
    first = False
    r, rec = run_case(NES, client, 'vm_' + cname, groups, ref, plist, ev, run_ms=112.0, dt=0.1, record=True, nes_name=name + '-')
    t = np.array(rec['t_ms'], float) - T0; msk = (t >= -5) & (t <= 110.0)
    tr = {}
    for nid, typ, role in roles:
        e = rec['neurons'][str(nid)]; vm = np.array(e['Vm_mV'] if isinstance(e, dict) else e, float)
        tr[str(nid)] = [round(float(x), 1) for x in vm[msk]]
    out['cases'][cname] = dict(label=lab, events=ev, cues=r['cues'], readback_mismatches=r['readback']['n_mismatch'], times_ms=[round(float(x), 2) for x in t[msk]], vm_mV=tr,
        spikes_all_neurons={str(k): v for k, v in r['spikes'].items() if v})
    ref_sp = raw['runs'][cname]['spikes']
    out['cases'][cname]['spikes_match_raster_run_within_112ms'] = all(sorted(x for x in r['spikes'].get(int(k), []) if x < 112) == sorted(x for x in v if x < 112) for k, v in ref_sp.items()) if True else None
    print(cname, 'samples', int(msk.sum()), 'match', out['cases'][cname]['spikes_match_raster_run_within_112ms'], flush=True)
json.dump(out, open(D + 'ripple_vm_mech.json', 'w'), separators=(',', ':'))
import os; print('size', os.path.getsize(D + 'ripple_vm_mech.json'))
