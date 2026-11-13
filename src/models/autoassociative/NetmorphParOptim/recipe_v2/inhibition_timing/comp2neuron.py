"""Map compartment ID -> neuron index by parsing the per-neuron flat blocks (LIFCNeuronStructFlatHeader) at the end of a saved model file."""
import sys, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
from gabafile import *
def neuron_flats(path):
    cls,h,off=locate(path)
    start=off+72*h['Rec']
    mm=np.memmap(path,dtype='u1',mode='r')
    rest=np.frombuffer(mm[start:start+4*((len(mm)-start)//4)].tobytes(),dtype='<u4')
    N=h['Neu']
    for i in range(0,min(len(rest)-10,2000000)):
        H=rest[i+2]
        if not(100<=H<=600) or rest[i]<=H: continue
        pos=i; ok=True; blocks=[]
        for k in range(N):
            if pos+10>len(rest) or rest[pos+2]!=H or rest[pos]<H: ok=False;break
            blocks.append((pos,int(rest[pos]))); pos+=int(rest[pos])//4
        if ok: return start+4*i, rest, blocks, H
    raise RuntimeError('flats not found')
def comp_map(path):
    st,rest,blocks,H=neuron_flats(path)
    ncomp=int(max(0,0)); m={}
    out=[]
    for k,(p,sz) in enumerate(blocks):
        hd=rest[p:p+9]
        so,do,ao=int(hd[4]),int(hd[6]),int(hd[8]); ns,nd,na=int(hd[3]),int(hd[5]),int(hd[7])
        b=rest[p:p+sz//4]
        ids=np.frombuffer(b.tobytes(),dtype='<i4')
        sid=ids[so//4:so//4+ns]; did=ids[do//4:do//4+nd]; aid=ids[ao//4:ao//4+na]
        out.append((sid,did,aid))
    return out
if __name__=='__main__':
    o=comp_map('/var/lib/BrainGenix/NES/Admonishing/Models/v2-arbor-S10000')
    print(len(o),[ (len(a),len(b),len(c)) for a,b,c in o[:3]], o[0][0][:5], o[0][1][:5], o[0][2][:5])
