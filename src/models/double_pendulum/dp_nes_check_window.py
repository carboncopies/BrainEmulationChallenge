"""dp_nes_check_window.py: phase 3b. Does the windowed GetSpikeTimes (SinceTime_ms + NeuronIDs)
return exactly the output spikes the full read returns for the same window?

Per tick: schedule + RunFor as dp_nes does, then ONE full read and ONE windowed read of the same
state. New spikes by the full read = the part of each output neuron's history beyond what it had
before. Compared per neuron as exact lists (times), for window offsets 0 and 0.5 ms.
  python3 dp_nes_check_window.py [--ticks 40] [--out output/window_check.json]
"""
import argparse
import json
import os

import numpy as np

import dp_nes
from dp_spiking import load_recipe, STEPS

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticks', type=int, default=40)
    ap.add_argument('--out', default=os.path.join(HERE, 'output', 'window_check.json'))
    a = ap.parse_args()
    rec = load_recipe()
    ctl, net = dp_nes.make_controller('johnjose-dp-wincheck', seed=0, rec=rec, read='none')
    L = ctl.loop
    sig = np.array(rec['sigma'])
    rng = np.random.default_rng(1)
    prev = {i: 0 for i in L.out_ids}
    res = dict(ticks=a.ticks, per_tick=[])
    ok = {0.0: True, 0.5: True}
    for k in range(1, a.ticks + 1):
        t0 = L.t_ms                                  # tick start; tick() advances it
        ctl(0.5 * sig * rng.standard_normal(6))      # read='none': schedule + run only
        full = L.sim.GetSpikeTimes()['SpikeTimes']
        want = {}
        for nid in L.out_ids:
            h = full[str(nid)]['tSpike_ms']
            want[nid] = h[prev[nid]:]
            prev[nid] = len(h)
        row = dict(tick=k, t0=t0, n_new=sum(len(v) for v in want.values()))
        for off in (0.0, 0.5):
            resp, nbytes = L._windowed_request(t0 + off)
            got = {nid: resp['SpikeTimes'][str(nid)]['tSpike_ms'] for nid in L.out_ids}
            same = got == want
            ok[off] &= same
            row['off%.1f' % off] = dict(n=sum(len(v) for v in got.values()), exact=same, bytes=nbytes)
        row['full_bytes'] = L.raw_history_probe()['bytes']
        res['per_tick'].append(row)
        if k % 10 == 0 or not row['off0.5']['exact']:
            print(row, flush=True)
    res['exact_offset_0.0'], res['exact_offset_0.5'] = ok[0.0], ok[0.5]
    res['total_new_spikes'] = sum(r['n_new'] for r in res['per_tick'])
    json.dump(res, open(a.out, 'w'), indent=1)
    print('exact (offset 0.0):', ok[0.0], ' exact (offset 0.5):', ok[0.5], ' spikes compared:', res['total_new_spikes'])
