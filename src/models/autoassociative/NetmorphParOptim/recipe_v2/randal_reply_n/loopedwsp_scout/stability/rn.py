"""Reduced-network model of the completed 17-cell assembly (OFFLINE analysis; no NES call, no sim).
Cell = copy of cell_offline.py / LIFCNeuron.cpp (exp-Euler, fAHP, sAHP with AHPCLIP min(sum,gmax), adaptive threshold h and floor, reset TOVM/AFTER).
Synapses (Netmorph build constants, gaba_nmda_api/FINDINGS.md, nmda_gaba_exp/figs.py): AMPA rise 0.5 / decay 3 ms E 0; NMDA rise 2 / decay 100 ms E 0 with
Mg block B(V)=1/(1+0.33 exp(-0.062 V)); GABA rise 0.5 / decay 10 ms E -70; onset delay 1 ms; peak-normalised kernels; one spike of j adds the pair's
programmed g_peak_sum (nS) at its peak.  Only the 17 members are simulated (non-member Pyr are ~silent in the stored runs); interneuron feedback is ONE
free parameter kappa (nS added to every member's GABA per member spike, delay 1+DI ms), because Pyr->Int and Int->Pyr conductances are not stored.
Weights: the exact programmed matrices (fllib Net + pwlib.arm_matrix = what run_pl/run_pw programmed), NMDA = min(r * AMPA, 0.5612 * G) (grown NMDA peak cap).
All events of a run are simulated in one batch (E, N)."""
import sys, json
import numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn')
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue')
import fllib as FL, pwlib as PW
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
P = dict(Vrest=-70., Vth=-50., Rm=100., Cm=100., refr=2., Vsp=30., EAHP=-90.)
FAHP = (2.5, 30., 3., 5.)          # rise, decay, g, gmax (nS)   model file
SAHP0 = (30., 300., 1., 2.)        # LH / N0
NMDA_CAP = 0.5612                  # grown NMDA peak / AMPA peak per pair (0.55/0.98 nS per synapse)
def knorm(tr, td): tp = tr * td / (td - tr) * np.log(td / tr); return np.exp(-tp / td) - np.exp(-tp / tr)

def member_matrices(key, arm, A, r=1.0):
    net = FL.Net(key)
    if arm == 'L0': X, info = FL.build_F(net, [A], None)
    else: X, info = PW.arm_matrix(net, A, arm)
    A = list(A); XA = X[np.ix_(A, A)].copy(); np.fill_diagonal(XA, 0)
    GA = net.G[np.ix_(A, A)].copy(); XN = np.minimum(r * XA, NMDA_CAP * GA); np.fill_diagonal(XN, 0)
    nonm = [i for i in range(96) if i not in set(A)]
    return dict(XA=XA, XN=XN, member_input=X[:, A].sum(0), bg_in=X[np.ix_(nonm, A)].sum(0), X=X, net=net, A=A)

def sim(XA, XN, cues_list, XG=None, npyr=17, reset='TOVM', Vreset=-55., sahp=SAHP0, fahp=FAHP, T=450., dt=0.05, ext=None,
        delay=1.0, kgain=1.0, ggain=1.0):
    """cues_list: list over events of [(t_ms, member_index), ...]. returns spike raster (steps, E, N) uint8 and time axis.
    ext: optional (E, N, steps) external conductance (AMPA-like) per cell. kgain scales all recurrent conductances (for sweeps)."""
    N = XA.shape[0]; E = len(cues_list); S = int(T / dt); gL = 1000. / P['Rm']
    if XG is None: XG = np.zeros((N, N))
    sgv = np.where(np.arange(N) < npyr, sahp[2], 0.)[None, :]; sgmv = np.where(np.arange(N) < npyr, sahp[3], 0.)[None, :]
    nfA, nfN, nfG = knorm(.5, 3.), knorm(2., 100.), knorm(.5, 10.); nff = knorm(FAHP[0], FAHP[1]); fr_, fd_, fg, fgm = fahp; sr_, sd_ = sahp[0], sahp[1]; nfs = knorm(sr_, sd_)
    dA = (np.exp(-dt / 3.), np.exp(-dt / .5)); dN = (np.exp(-dt / 100.), np.exp(-dt / 2.)); dG = (np.exp(-dt / 10.), np.exp(-dt / .5))
    dFd, dFr = np.exp(-dt / fd_), np.exp(-dt / fr_); dSd, dSr = np.exp(-dt / sd_), np.exp(-dt / sr_)
    z = lambda: np.zeros((E, N)); sAd, sAr, sNd, sNr, sGd, sGr, fAd, fAr, sSd, sSr = [z() for _ in range(10)]
    V = np.full((E, N), P['Vrest']); h = np.ones((E, N)); fl = np.full((E, N), P['Vth']); tl = np.full((E, N), -1e9); done = np.ones((E, N), bool); vr = np.full((E, N), P['Vth'])
    nd = int(round(delay / dt)); buf = np.zeros((nd + 2, E, N), np.float64); raster = np.zeros((S, E, N), np.uint8)
    cue_at = {}
    for e, cl in enumerate(cues_list):
        for (t, m) in cl: cue_at.setdefault(int(round(t / dt)), []).append((e, m))
    XAt, XNt, XGt = XA * kgain, XN * kgain, XG * ggain; L = len(buf)
    for k in range(S):
        t = k * dt; sd = buf[(k - nd) % L] if k >= nd else None
        if sd is not None:
            ia = sd @ XAt; inn = sd @ XNt; sAd += ia; sAr += ia; sNd += inn; sNr += inn
            ig = sd @ XGt; sGd += ig; sGr += ig
        sAd *= dA[0]; sAr *= dA[1]; sNd *= dN[0]; sNr *= dN[1]; sGd *= dG[0]; sGr *= dG[1]; fAd *= dFd; fAr *= dFr; sSd *= dSd; sSr *= dSr
        gA = (sAd - sAr) / nfA; gN = (sNd - sNr) / nfN; gI = (sGd - sGr) / nfG
        if ext is not None: gA = gA + ext[:, :, k]
        gf = np.minimum(fg * (fAd - fAr) / nff, fgm); gs = np.minimum(sgv * (sSd - sSr) / nfs, sgmv)
        B = 1. / (1. + 0.33 * np.exp(-0.062 * V)); gNB = gN * B
        gt = gL + gf + gs + gA + gNB + gI
        Vinf = (gL * P['Vrest'] + (gf + gs) * P['EAHP'] + gI * (-70.)) / gt
        V = Vinf + (V - Vinf) * np.exp(-dt * gt / P['Cm'])
        h += (1 - h) * dt / 50.; fl = P['Vth'] + (fl - P['Vth']) * np.exp(-dt / 500.)
        thr = np.maximum(P['Vth'] + 10. * (1 - h), fl)
        ok = t >= tl + P['refr']
        rel = ok & ~done; V = np.where(rel, vr, V); done = done | rel
        spk = ok & (V >= thr)
        if k in cue_at:
            for (e, m) in cue_at[k]: spk[e, m] = True
        if spk.any():
            vr = np.where(spk, (np.minimum(V, P['Vth']) if reset == 'TOVM' else Vreset), vr)
            tl = np.where(spk, t, tl); V = np.where(spk, P['Vsp'], V); done = np.where(spk, False, done); h = np.where(spk, h - 0.2, h); fl = np.where(spk, fl + 1., fl)
            fAd += spk; fAr += spk; sSd += spk; sSr += spk; raster[k] = spk; buf[k % L] = spk
        else: buf[k % L] = 0
    return raster

def load_run(tag, prefix):
    d = json.load(open(HERE + '%s%s.json' % (prefix, tag))); return d
def events_cues(d, A):
    idx = {c: i for i, c in enumerate(A)}; out = []; meta = []
    for e in d['events']:
        out.append([(t - e['t'], idx[c]) for (t, c) in e['cues'] if c in idx]); meta.append(e)
    return out, meta
def stored_measures(d, A):
    """measures of the stored run, MEMBER spikes only (the reduced model has no non-members). window definitions as analyze_pw.py"""
    sp = {int(k): np.array(sorted(v)) for k, v in d['spikes'].items()}; rows = []
    def w(i, a, b): x = sp.get(i); return x[(x >= a) & (x < b)] if x is not None else np.array([])
    allpyr = np.sort(np.concatenate([sp[i] for i in sp if i < 96])) if any(i < 96 for i in sp) else np.array([])
    for e in d['events']:
        t = e['t']; cue = set(e['cue']); nonc = [m for m in A if m not in cue]
        cont = ((allpyr >= t - 1500) & (allpyr < t)).sum() > 60
        mem = [w(m, t, t + 450) - t for m in A]; allm = np.concatenate(mem) if mem else np.array([])
        r = dict(kind=e['kind'], cont=bool(cont), complete=bool(all(len(w(m, t, t + 30)) > 0 for m in nonc)) if e['kind'] != 'unrel' else False,
                 recruit=bool(any(len(w(m, t, t + 30)) > 0 for m in nonc)), mem450=int(len(allm)), last=float(allm.max()) if len(allm) else 0.,
                 late=int(sum(len(w(m, t + 15, t + 450)) for m in A)), nm450=int(sum(len(w(i, t, t + 450)) for i in range(96) if i not in set(A))))
        r['reverb'] = r['mem450'] > 50; rows.append(r)
    return rows
def sim_measures(raster, meta, A, dt=0.05):
    rows = []; tt = np.arange(raster.shape[0]) * dt
    for e, ev in enumerate(meta):
        R = raster[:, e, :]; cue = set(ev['cue']); idx = {c: i for i, c in enumerate(A)}; nonc = [idx[m] for m in A if m not in cue]
        in30 = (tt < 30); comp = bool(all(R[in30, m].any() for m in nonc)) if ev['kind'] != 'unrel' else False
        rec = bool(any(R[in30, m].any() for m in nonc)); late = int(R[(tt >= 15)].sum()); tot = int(R.sum()); lastt = float(tt[R.any(1)].max()) if R.any() else 0.
        rows.append(dict(kind=ev['kind'], complete=comp, recruit=rec, mem450=tot, last=lastt, late=late, reverb=tot > 50))
    return rows

def full_matrices(M, nI=7, gPI=1.0, gIP=1.0):
    """members + nI interneuron cells: Pyr->Int AMPA gPI nS per pair (no NMDA onto Int, nmda_gaba_exp README), Int->Pyr GABA gIP nS per pair."""
    n = M['XA'].shape[0]; N = n + nI; XA = np.zeros((N, N)); XN = np.zeros((N, N)); XG = np.zeros((N, N))
    XA[:n, :n] = M['XA']; XN[:n, :n] = M['XN']; XA[:n, n:] = gPI; XG[n:, :n] = gIP
    return XA, XN, XG
def run_model(M, cl, nI=7, gPI=1.0, gIP=1.0, **kw):
    XA, XN, XG = full_matrices(M, nI, gPI, gIP); return sim(XA, XN, cl, XG=XG, npyr=M['XA'].shape[0], **kw)
def pop_bins(R, e, n=17, dt=0.05, width=50., T=450.):
    ts = np.nonzero(R[:, e, :n].sum(1))[0]; w = R[:, e, :n].sum(1)[ts]; return np.histogram(ts * dt, bins=np.arange(0, T + 1, width), weights=w)[0]
def stored_bins(d, A, meta_idx, width=50., T=450.):
    sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; e = d['events'][meta_idx]; t = e['t']
    ts = np.concatenate([sp[m][(sp[m] >= t) & (sp[m] < t + T)] - t for m in A if m in sp] + [np.array([])]); return np.histogram(ts, bins=np.arange(0, T + 1, width))[0]
