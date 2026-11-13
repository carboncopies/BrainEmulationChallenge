"""usage: run_arbor.py VARIANT(E1|NI|E1d) KIND ...  KIND: single | rip:NAME:order:spacing:dt[:rec] ; K=4 groups from design_K4.json"""
import sys, json, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA')
from alib import *
variant = sys.argv[1]; kinds = sys.argv[2:]
groups = groups_from(OUT + 'design_K4.json')
NES, client = L.connect()
fn = OUT + 'raw_%s.json' % variant
out = json.load(open(fn)) if __import__('os').path.exists(fn) else dict(variant=variant, groups=[dict(members=m, cue=c) for m, c in groups], runs={})
for kind in kinds:
    p = kind.split(':')
    if p[0] == 'single':
        evs = []; t = 0.0
        for gi, (mem, cue) in enumerate(groups):
            evs.append(dict(label='G%d full 4-cell' % gi, group=gi, cue=list(cue), t=t, expect=True)); t += 500
            evs.append(dict(label='G%d 3-cell a' % gi, group=gi, cue=list(cue[:3]), t=t, expect=False)); t += 500
            evs.append(dict(label='G%d 3-cell b' % gi, group=gi, cue=list(cue[1:]), t=t, expect=False)); t += 500
        cues = [(e['t'] + o, c) for e in evs for c, o in zip(e['cue'], CUE_OFFS)]
        spikes, rec, rb, load = run_sim(NES, client, variant + '-single', groups, variant, cues, t + 100, 1.0)
        res = []
        for e in evs:
            gi = e['group']; mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]; t0 = e['t']
            w = lambda i: [x - t0 for x in spikes.get(i, []) if t0 <= x < t0 + 450]
            fired = [m for m in nc if w(m)]
            otherg = [m for g2, (mm, _) in enumerate(groups) if g2 != gi for m in mm if w(m)]
            allmem = {m for mm, _ in groups for m in mm}
            op = [i for i in range(NP) if i not in allmem and w(i)]
            lat = min((x for m in fired for x in w(m)), default=None)
            res.append(dict(label=e['label'], cue=e['cue'], expect_complete=e['expect'], noncue_fired=len(fired), noncue_total=len(nc), latency_ms=lat,
                member_spikes=sum(len(w(m)) for m in mem), other_group_members_fired=len(otherg), other_pyr_fired=len(op),
                interneuron_spikes=sum(len(w(i)) for i in range(NP, N)), ints_fired=[i for i in range(NP, N) if w(i)],
                last_pyr_spike_ms=max((x for i in range(NP) for x in w(i)), default=None),
                clean=bool((len(fired) == len(nc) if e['expect'] else len(fired) == 0) and not otherg and not op)))
            print(variant, res[-1]['label'], res[-1]['noncue_fired'], res[-1]['latency_ms'], res[-1]['member_spikes'], res[-1]['interneuron_spikes'], res[-1]['clean'], flush=True)
        out['runs']['single'] = dict(events=res, readback=rb, load=load, spikes={str(k): v for k, v in spikes.items() if v})
    else:
        _, name, order, sp, dt = p[:5]; recflag = len(p) > 5
        order = [int(c) for c in order]; sp = float(sp); dt = float(dt)
        ev = [(g, i * sp) for i, g in enumerate(order)]
        run_ms = 150.0
        spikes, rec, rb, load = run_sim(NES, client, '%s-%s' % (variant, name), groups, variant, ripple_cues(groups, ev), run_ms, dt, record=recflag)
        a = analyse_ripple(ev, spikes, groups)
        entry = dict(events=ev, dt_ms=dt, analysis=a, readback=rb, load=load, spikes={str(k): v for k, v in spikes.items() if v})
        if recflag:
            t = np.array(rec['t_ms'], float) - T0; lo, hi = (-5, 110)
            msk = (t >= lo) & (t <= hi)
            allm = [m for mm, _ in groups for m in mm]
            # interneurons: those that fired, plus the 6 most driven by memory members (programmed drive), drivable only
            cond = {(x, y): c for x, y, c, g in build(groups, variant)[1]}
            dr = sorted(dump.its, key=lambda i: -sum(cond.get((m, i), 0.0) for m in allm))[:8]
            ints = sorted(set(dr) | set(a['ints_that_fired']))
            tr = {}
            for nid in allm + ints:
                e = rec['neurons'][str(nid)]; vm = np.array(e['Vm_mV'] if isinstance(e, dict) else e, float)
                tr[str(nid)] = [round(float(x), 1) for x in vm[msk]]
            entry['vm'] = dict(window_ms=[lo, hi], times_ms=[round(float(x), 2) for x in t[msk]], vm_mV=tr, pyramidal_memory_cells=allm, interneurons=ints, top_driven_ints=dr)
        out['runs'][name + ('_dt%g' % dt)] = entry
        print(variant, name, 'dt', dt, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms'], m['last_member_spike_after_cue_ms'], m['int_spikes_in_window']) for m in a['memories']],
              'spur', a['spurious_nonmember_pyr_spikes'], 'ct', len(a['crosstalk_events']), 'end', a['last_any_spike_ms'], 'succ', a['ripple_success'], flush=True)
    json.dump(out, open(fn, 'w'), separators=(',', ':'))
    time.sleep(15)
