#!/usr/bin/env python3
"""pong_netmorph_grow.py: grow the Pong controller topology with Netmorph in NES,
save it as a model and dump a connectome summary JSON for pong_netmorph_analyze.py.

  python pong_netmorph_grow.py -Port 8100 -Variant edge -Model johnjose-pong-grown
"""
import argparse
import json
import os
import sys
import time

import nes_loop as NL
import pong_netmorph_config as C


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Variant', default='edge', choices=['edge', 'class'])
    p.add_argument('-PType', default='interneuron', choices=['interneuron', 'pyramidal'])
    p.add_argument('-DSyn', default=2.0, type=float, help='D_synmax (um) for the pyr/int type pairs')
    p.add_argument('-YStep', default=None, type=float, help='um between bins (default pong_spec.Y_STEP=50)')
    p.add_argument('-XStage', default=None, type=float)
    p.add_argument('-ConfigFile', default=None, help='use this config file instead of generating one')
    p.add_argument('-Model', default='johnjose-pong-grown')
    p.add_argument('-Out', default='output')
    return p.parse_args(argv)


def dump_summary(sim, path, extra):
    """Connectome summary used by analysis/tuning (all from the client API)."""
    ab = sim.GetAbstractConnectome(Sparse=True)
    full = sim.GetConnectome()
    pos = sim.GetSomaPositions()
    summ = dict(extra)
    summ['Regions'] = ab['Regions']
    summ['PrePostNumReceptors'] = ab['PrePostNumReceptors']
    summ['Connectome'] = full
    summ['SomaPositions'] = pos
    json.dump(summ, open(path, 'w'))
    return summ


def main(argv=None):
    A = parse_args(argv)
    os.makedirs(A.Out, exist_ok=True)
    if A.ConfigFile:
        content = open(A.ConfigFile).read()
    else:
        content = C.make(A.Variant, A.PType, A.DSyn, A.YStep, A.XStage)
    cfgpath = os.path.join(A.Out, '%s.cfg' % A.Model)
    open(cfgpath, 'w').write(content)
    client = NL.connect(A.Host, A.Port)
    sim = NL.new_simulation(client, 'Netmorph-' + A.Model, seed=0)
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)  # before receptors are built
    sim.SetSTDP(_DoSTDP=False)
    t0 = time.time()
    r = sim.Netmorph_RunAndWait(content, _NeuronClass='LIFC')
    grow_s = time.time() - t0
    print('Netmorph finished: %s in %.0f s' % (r, grow_s))
    if not r['Success']:
        print('growth FAILED', getattr(sim, 'NetmorphError', ''))
        return 1
    sim.ModelSave(A.Model)
    print('saved model', A.Model)
    summ = dump_summary(sim, os.path.join(A.Out, '%s_connectome.json' % A.Model),
                        dict(model=A.Model, variant=A.Variant, ptype=A.PType, dsyn=A.DSyn, ystep=A.YStep, xstage=A.XStage, grow_seconds=grow_s,
                             netmorph_output_dir=r['NetmorphOutputDirectory'], config=cfgpath))
    print('regions:', {k: v for k, v in summ['Regions'].items()})
    print('neuron-neuron pairs with synapses: %d' % len(summ['PrePostNumReceptors']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
