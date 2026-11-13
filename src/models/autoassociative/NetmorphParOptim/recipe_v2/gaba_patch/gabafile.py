"""Reader/patcher for NES saved-model files (LIFC). Receptor record = LIFCReceptorBase, 72 bytes (Receptor.h:88-112):
 int ID, ShapeID, SrcComp, DstComp; float Erev, Rise, Decay, PeakG_nS, Weight, OnsetDelay; bool voltage_gated(+3 pad);
 int STDP_Method; float A_pos, A_neg, Tau_pos, Tau_neg, Shift; int NT (0 AMPA,1 GABA,2 NMDA).
Header = SaveLoadPrior(int 4 B) + SaverInfo(9 x size_t). Receptor array start is located by validating the struct pattern
(geometry structs contain vtable pointers so their sizes are inferred from the file, not compiled)."""
import numpy as np, struct
RDT = np.dtype([('ID','<i4'),('Shape','<i4'),('Src','<i4'),('Dst','<i4'),('Erev','<f4'),('Rise','<f4'),('Decay','<f4'),('G','<f4'),('W','<f4'),('Delay','<f4'),('vg','u1'),('pad','u1',3),('STDP','<i4'),('Ap','<f4'),('An','<f4'),('Tp','<f4'),('Tn','<f4'),('Sh','<f4'),('NT','<i4')])
assert RDT.itemsize == 72
def header(path):
    with open(path,'rb') as f: b = f.read(4+72)
    cls = struct.unpack('<i', b[:4])[0]; info = struct.unpack('<9Q', b[4:76])
    return cls, dict(zip(['SG','Sph','Cyl','Box','Comp','Rec','Neu','Reg','Circ'], info))
def locate(path):
    cls, h = header(path); n = h['Rec']
    mm = np.memmap(path, dtype='u1', mode='r')
    base = 76 + 16*h['SG']  # SaverGeometry = enum(4)+pad(4)+size_t(8)
    nw = (len(mm) - base)//4
    words = np.frombuffer(mm[base:base+nw*4], dtype='<i4')
    # candidates: word0==0 and words at +18,+36,+54 == 1,2,3 (IDs spaced 72 B)
    m = (words[:-54] == 0) & (words[18:-36] == 1) & (words[36:-18] == 2) & (words[54:] == 3)
    best = None
    for i in np.where(m)[0]:
        o = base + 4*int(i)
        r = np.frombuffer(mm[o:o+72*3].tobytes(), dtype=RDT)
        if np.all(r['NT']<3) and np.all(r['G']>0): best = o; break
    assert best is not None, 'receptor array not found'
    return cls, h, best
def load(path):
    cls, h, off = locate(path)
    rec = np.memmap(path, dtype=RDT, mode='r', offset=off, shape=(h['Rec'],))
    return cls, h, off, rec
