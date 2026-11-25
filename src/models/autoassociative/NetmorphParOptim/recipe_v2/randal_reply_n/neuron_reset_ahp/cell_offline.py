#!/usr/bin/env python3
"""OFFLINE planning aid, not a result: one LIFC cell copied from LIFCNeuron.cpp (exp-Euler on Cm, reset options TOVM/AFTER, fAHP/sAHP with
AHPCLIP saturation (min(linear sum, gmax)), adaptive threshold h (0.2/spike, tau 50) and floor (+1 mV/spike, tau 500)). Omitted: ADP (0.3 nS,
no measurable effect in gaba_vm), spike-time triangulation. Input: constant AMPA-like conductance g_E (E 0 mV) for 400 ms, as a stand-in for
the recurrent drive during a reverberation. Prints spikes and last spike time per arm."""
import numpy as np
P = dict(Vrest=-70., Vth=-50., Rm=100., Cm=100., refr=2., Vsp=30., EAHP=-90., f=(2.5, 30., 3., 5.), s=(30., 300., 1., 2.))
def kern_norm(tr, td): tp = tr * td / (td - tr) * np.log(td / tr); return np.exp(-tp / td) - np.exp(-tp / tr)
def run(gE, reset='TOVM', Vreset=-55., s=(30., 300., 1., 2.), T=400., dt=0.05, pulse=None):
    gL = 1000. / P['Rm']; V = P['Vrest']; h = 1.; fl = P['Vth']; sp = []; tl = -1e9; vr = Vreset; done = True
    fr, fd, fg, fgm = P['f']; sr, sd, sg, sgm = s; nf = kern_norm(fr, fd); ns = kern_norm(sr, sd)
    for k in range(int(T / dt)):
        t = k * dt; S = np.array(sp)
        lf = fg * (((np.exp(-(t - S) / fd) - np.exp(-(t - S) / fr)) / nf).sum() if len(S) else 0.)
        ls = sg * (((np.exp(-(t - S) / sd) - np.exp(-(t - S) / sr)) / ns).sum() if len(S) else 0.)
        gf = min(lf, fgm); gs = min(ls, sgm); g = gE(t) if callable(gE) else gE
        gt = gL + gf + gs + g; Vinf = (gL * P['Vrest'] + (gf + gs) * P['EAHP'] + g * 0.) / gt
        V = Vinf + (V - Vinf) * np.exp(-dt * gt / P['Cm'])
        h += (1 - h) * dt / 50.; fl = P['Vth'] + (fl - P['Vth']) * np.exp(-dt / 500.)
        thr = max(P['Vth'] + 10. * (1 - h), fl)
        if t >= tl + P['refr']:
            if not done: V = vr; done = True
            if V >= thr:
                vr = min(V, P['Vth']) if reset == 'TOVM' else Vreset
                sp.append(t); tl = t; V = P['Vsp']; done = False; h -= 0.2; fl += 1.
    return np.array(sp)
ARMS = {'LH (TOVM, sAHP 1/2 nS, 300 ms)': dict(reset='TOVM'), 'R (AFTER -55)': dict(reset='AFTER'),
        'S2 (sAHP 2/4 nS, 1000 ms)': dict(reset='TOVM', s=(30., 1000., 2., 4.)), 'RS2': dict(reset='AFTER', s=(30., 1000., 2., 4.)),
        'RS3 (sAHP 3/6 nS, 1500 ms)': dict(reset='AFTER', s=(30., 1500., 3., 6.))}
if __name__ == '__main__':
    print('constant drive gE (nS): spikes in 400 ms / first ISI ms / last spike ms')
    for gE in (12., 16., 20., 30.):
        row = []
        for name, a in ARMS.items():
            s = run(gE, **a); row.append('%s: %d / %s / %s' % (name.split(' ')[0], len(s), '%.1f' % (s[1] - s[0]) if len(s) > 1 else '-', '%.0f' % s[-1] if len(s) else '-'))
        print('gE %4.0f | ' % gE + ' | '.join(row))
    # decaying drive: recurrent drive that falls when the cell's own rate falls is not modelled; a 50 ms pulse + weak tail
    print('pulse 25 nS for 50 ms then 12 nS tail: spikes / last spike')
    for name, a in ARMS.items():
        s = run(lambda t: 25. if t < 50 else 12., **a); print('  %-34s %3d  %s' % (name, len(s), '%.0f' % s[-1] if len(s) else '-'))
