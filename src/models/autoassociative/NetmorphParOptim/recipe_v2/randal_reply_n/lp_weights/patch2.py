p='lpw_lib.py'; s=open(p).read()
s=s.replace("    def __init__(self, G, theta, H, lbw):\n","    def __init__(self, G, theta, H, lbw, hubmode='exclude'):\n")
s=s.replace("        self.hubs = [int(j) for j in np.where(self.base.sum(0) > H + 1e-9)[0]]\n",
"        self.hubs = [int(j) for j in np.where(self.base.sum(0) > H + 1e-9)[0]]\n        self.hubmode = hubmode\n        self.hub_excl = set(self.hubs) if hubmode == 'exclude' else set()\n        if hubmode == 'waive': self.Hv[self.hubs] = 1e9   # NON-COMPLIANT with constraint 5; used only as the R3-comparable variant (R3 counts used the hub cells as targets)\n")
s=s.replace("        if n in cfg.hubs: continue\n","        if n in cfg.hub_excl: continue\n")
s=s.replace("VARIANTS = {'primary': PRIMARY,","VARIANTS = {'primary': PRIMARY, 'hubs_waived': dict(PRIMARY, hubmode='waive'),")
s=s.replace("hub_inputs=[round(float(inp[j]), 1) for j in cfg.hubs])","hub_inputs=';'.join('%d:%.1f' % (j, inp[j]) for j in cfg.hubs))")
open(p,'w').write(s)
