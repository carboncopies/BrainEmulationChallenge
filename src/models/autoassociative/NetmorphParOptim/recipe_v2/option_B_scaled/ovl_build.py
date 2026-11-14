"""Overlap-aware replacement for fable_design_S1/design.build (which assumes disjoint memories): base = background only; each memory's interior pairs are taken from
build([that memory]); a pair interior to several memories gets the max over those memories. Per-memory loop caps (8 nS per target) are therefore applied per memory; a shared cell can receive up to 8 nS from each memory's loop."""
import numpy as np
def install(dz):
    orig=dz.build
    def build(groups,**kw):
        W=orig([],**kw); Wm=[orig([g],**kw) for g in groups]; inter={}
        for gi,(mem,cue) in enumerate(groups):
            for a in mem:
                for b in mem:
                    if a!=b: inter[(a,b)]=max(inter.get((a,b),-1.0),Wm[gi][a,b])
        for (a,b),v in inter.items(): W[a,b]=v
        return W
    dz.build=build
