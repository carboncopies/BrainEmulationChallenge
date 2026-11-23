"""Reader/patcher for NES saved LIFC model files (patched build), extending ../../gaba_patch/gabafile.py.
Receptor record = LIFCReceptorBase (72 B, gabafile.RDT). Neuron = LIFCNeuronStructFlatHeader: 9 x uint32 (FlatBufSize, NameSize, NameOffset,
SomaN, SomaOff, DendN, DendOff, AxonN, AxonOff) + LIFCNeuronBase (38 x 4 B, Neuron.h) + name + int32 compartment ID lists.
Only ever applied to COPIES of a model; originals are opened read-only."""
import sys, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
from gabafile import RDT, header, locate
BASE = ['ID','Vrest','Vreset','Vth','Rm','Cm','Refr','SpikeDepol','UpdateMethod','ResetMethod','E_AHP',
        'fAHP_rise','fAHP_decay','fAHP_g','fAHP_gmax','fAHP_half','sAHP_rise','sAHP_decay','sAHP_g','sAHP_gmax','sAHP_half','AHPsat',
        'FatigueThr','FatigueRec','E_ADP','ADP_rise','ADP_decay','ADP_g','ADP_satmult','ADP_rec','ADP_depl','ADPsat',
        'AT_dps','AT_rec','AT_dpot','AT_floor','AT_floor_dps','AT_floor_rec']
INTF = {'ID','UpdateMethod','ResetMethod','AHPsat','ADPsat'}
NDT = np.dtype([('hdr','<u4',9)] + [(n, '<i4' if n in INTF else '<f4') for n in BASE])
assert NDT.itemsize == 36 + 152
def neurons(path, nexp):
    """returns list of (offset, struct ndarray view info, soma ids, dend ids, axon ids) for nexp neurons, located by header pattern."""
    mm = np.memmap(path, dtype='u1', mode='r')
    cls, h, roff = locate(path)
    start = roff + 72 * h['Rec']
    tail = np.frombuffer(mm[start:].tobytes()[: (len(mm) - start) // 4 * 4], dtype='<u4')
    # candidates: NameOffset (word 2) == 188, ID word (9) == 0
    c = np.where((tail[2:] == 188) & (tail[9:].view('<i4')[:len(tail)-9][:len(tail)-2] if False else True))[0]
    out = []; pos = None
    for i in np.where(tail[2:-7] == 188)[0]:
        if tail[i + 9] == 0: pos = start + 4 * int(i); break
    assert pos is not None, 'neuron flats not found'
    for k in range(nexp):
        rec = np.frombuffer(mm[pos:pos + 188].tobytes(), dtype=NDT)[0]
        hd = rec['hdr']; assert hd[2] == 188 and rec['ID'] == k, (k, hd, rec['ID'])
        def ids(n, o): return np.frombuffer(mm[pos + o: pos + o + 4 * n].tobytes(), dtype='<i4').copy()
        out.append(dict(off=pos, rec=rec, soma=ids(hd[3], hd[4]), dend=ids(hd[5], hd[6]), axon=ids(hd[7], hd[8])))
        pos += int(hd[0])
    return h, roff, out
def comp2neuron(nl):
    m = {}
    for k, n in enumerate(nl):
        for a in ('soma', 'dend', 'axon'):
            for c in n[a]: m[int(c)] = k
    return m
