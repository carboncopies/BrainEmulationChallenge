"""Core-statistics tests on a tiny synthetic model (hand-computable numbers), plus round trips through both input adapters.
Run: python3 -m unittest discover -s tests -v   (from the realism_tester folder)."""
import os, sys, json, struct, tempfile, unittest, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from rt.model import Model, AXON, DEND, UNCL
from rt import stats, grids, compare, io_netmorph, io_nes, report

# 3 cells on the x axis: cell 0 'exc' at (0,0,0), cell 1 'exc' at (100,0,0), cell 2 'inh' at (0,100,0)
SOMA = [[0, 0, 0], [100, 0, 0], [0, 100, 0]]; TYPES = ['exc', 'exc', 'inh']
# segments (cell, kind, p0, p1)
SEGS = [(0, AXON, [0, 0, 0], [30, 0, 0]), (0, AXON, [30, 0, 0], [30, 40, 0]),      # cell 0 axon: 30 + 40 = 70, reach max |(30,40,0)| = 50
        (0, DEND, [0, 0, 0], [0, 0, 10]),                                          # cell 0 dendrite 10, reach 10
        (1, AXON, [100, 0, 0], [100, 20, 0]),                                      # cell 1 axon 20, reach 20
        (1, DEND, [100, 0, 0], [110, 0, 0]), (1, DEND, [110, 0, 0], [130, 0, 0]),  # cell 1 dendrite 30, reach 30
        (2, AXON, [0, 100, 0], [0, 160, 0]),                                       # cell 2 axon 60, reach 60
        (2, DEND, [0, 100, 0], [0, 100, -5])]                                      # cell 2 dendrite 5, reach 5
# contacts: 0->1 x2, 0->2 x1, 1->0 x1, 2->0 x3, 2->1 x1, 0->0 x1 (autapse)
SYN = [(0, 1, 1), (0, 1, 1), (0, 2, 1), (1, 0, 1), (2, 0, -1), (2, 0, -1), (2, 0, -1), (2, 1, -1), (0, 0, 1)]

def tiny(region=None):
    c = [s[0] for s in SEGS]; k = [s[1] for s in SEGS]; p0 = [s[2] for s in SEGS]; p1 = [s[3] for s in SEGS]
    pre = [s[0] for s in SYN]; post = [s[1] for s in SYN]; sign = [s[2] for s in SYN]; xyz = [[1, 1, 1]] * len(SYN)
    return Model(TYPES, SOMA, [5, 5, 5], c, k, p0, p1, None, pre, post, xyz, sign, region, {})

class TestStats(unittest.TestCase):
    def setUp(self): self.m, self.info = None, None; self.r, self.info = stats.compute(tiny(dict(volume_um3=1e6, name='r', shape='box', source='test')))
    def test_proportions_volume(self):
        self.assertAlmostEqual(self.r['proportion.exc']['mean'], 2 / 3); self.assertAlmostEqual(self.r['proportion.inh']['mean'], 1 / 3)
        self.assertAlmostEqual(self.r['cells_per_volume']['mean'], 3 / 1e-3)          # 1e6 um^3 = 1e-3 mm^3
        self.assertAlmostEqual(self.r['cells_per_volume.exc']['mean'], 2 / 1e-3)
    def test_lengths_mean_median(self):
        a = self.r['length.axon.exc']; self.assertEqual(a['n'], 2); self.assertAlmostEqual(a['mean'], 45); self.assertAlmostEqual(a['median'], 45); self.assertAlmostEqual(a['max'], 70)
        self.assertAlmostEqual(self.r['length.dendrite.exc']['mean'], 20); self.assertAlmostEqual(self.r['length.axon.inh']['mean'], 60)
    def test_reach(self):
        self.assertAlmostEqual(self.r['reach_max.axon.exc']['mean'], 35); self.assertAlmostEqual(self.r['reach_max.axon.exc']['max'], 50)
        self.assertAlmostEqual(self.r['reach_max.dendrite.exc']['mean'], 20)
        # cell 2 axon: one segment 0..60 along y -> length-weighted mean distance of midpoints = 30
        self.assertAlmostEqual(self.r['reach_mean.axon.inh']['mean'], 30)
    def test_targets_sources(self):
        # targets (no autapse): cell0 -> {1,2} = 2, cell1 -> {0} = 1, cell2 -> {0,1} = 2
        self.assertAlmostEqual(self.r['targets.exc']['mean'], 1.5); self.assertAlmostEqual(self.r['targets.inh']['mean'], 2)
        self.assertAlmostEqual(self.r['targets.exc.to.exc']['mean'], 1.0); self.assertAlmostEqual(self.r['targets.exc.to.inh']['mean'], 0.5)
        # sources: cell0 <- {1,2} = 2, cell1 <- {0,2} = 2, cell2 <- {0} = 1
        self.assertAlmostEqual(self.r['sources.exc']['mean'], 2); self.assertAlmostEqual(self.r['sources.inh']['mean'], 1)
        self.assertAlmostEqual(self.r['sources.exc.from.inh']['mean'], 1)
    def test_synapse_counts(self):
        # outgoing incl. autapse: cell0 = 4, cell1 = 1, cell2 = 4 ; incoming: cell0 = 1+3+1 = 5, cell1 = 3, cell2 = 1
        self.assertAlmostEqual(self.r['syn_axon.exc']['mean'], 2.5); self.assertAlmostEqual(self.r['syn_axon.inh']['mean'], 4)
        self.assertAlmostEqual(self.r['syn_dendrite.exc']['mean'], 4); self.assertAlmostEqual(self.r['syn_dendrite.inh']['mean'], 1)
        self.assertAlmostEqual(self.r['syn_dendrite.exc.from.inh']['mean'], 2)        # cell0 3, cell1 1
        self.assertEqual(self.info['n_autapse_contacts'], 1); self.assertAlmostEqual(self.r['autapses.exc']['mean'], 0.5)
    def test_pairs(self):
        self.assertAlmostEqual(self.r['conn_prob.exc.to.exc']['mean'], 1.0)          # 0->1 and 1->0 of 2 possible
        self.assertAlmostEqual(self.r['conn_prob.inh.to.exc']['mean'], 1.0); self.assertAlmostEqual(self.r['conn_prob.exc.to.inh']['mean'], 0.5)
        sp = self.r['syn_per_pair.exc.to.exc']; self.assertEqual(sp['n'], 2); self.assertAlmostEqual(sp['mean'], 1.5)    # 0->1: 2, 1->0: 1
        self.assertAlmostEqual(self.r['syn_per_pair.inh.to.exc']['median'], 2)       # pairs 2->0: 3, 2->1: 1

class TestGrids(unittest.TestCase):
    def test_length_conserved_and_units(self):
        m = tiny(); G, meta, prof = grids.build(m, voxel=10.0, rbin=10.0)
        for kn in ('axon', 'dendrite'):
            self.assertAlmostEqual(meta['length_check_um']['segments'][kn], meta['length_check_um']['deposited'][kn], places=3)
        self.assertAlmostEqual(G['axon_length.all'].sum() * 1000, 150, places=3)      # 70 + 20 + 60 um, density in um/um^3 x 1000 um^3
        self.assertAlmostEqual(G['soma.all'].sum() * 1000 * 1e-9, 3, places=6)
    def test_ball_index(self):
        # many radial segments: a centre-heavy 'ball' must give an index far above 1, a uniform ring of segments near 1
        rng = np.random.default_rng(0); n = 4000
        ang = rng.uniform(0, 2 * np.pi, n); r_ball = np.abs(rng.normal(0, 15, n)); r_uni = np.sqrt(rng.uniform(0, 120 ** 2, n))
        def mk(rr):
            p0 = np.c_[rr * np.cos(ang), rr * np.sin(ang), np.zeros(n)]; p1 = p0 + [1, 0, 0]
            return Model(['a'], [[0, 0, 0]], [5], np.zeros(n, int), np.zeros(n, int), p0, p1, None, [], [], np.zeros((0, 3)), [],
                         dict(center=[0, 0, 0], radius=120.0, thickness=30.0, volume_um3=1.0, shape='disc', source='t'), {})
        b = grids.build(mk(r_ball), 10.0)[2]['ball_index']['axon.a']; u = grids.build(mk(r_uni), 10.0)[2]['ball_index']['axon.a']
        self.assertGreater(b, 20); self.assertTrue(0.7 < u < 1.4, u)
    def test_quantise_roundtrip(self):
        g = np.zeros((4, 3, 2), np.float32); g[1, 2, 1] = 5.0; g[3, 0, 0] = 0.01; d = report.quantise(g); back = report.dequantise(d, (4, 3, 2))
        self.assertAlmostEqual(back[1, 2, 1], 5.0, places=4); self.assertAlmostEqual(back[3, 0, 0], 0.01, delta=0.01 * 0.05); self.assertEqual(back[0, 0, 0], 0)

class TestCompare(unittest.TestCase):
    def test_status_and_type_map(self):
        prof = dict(name='t', type_map={'exc': 'pyr', 'inh': 'int'}, defaults=dict(tolerance_rel=0.5, sd_k=2.0), comments={},
                    literature=[dict(metric='length.axon.pyr', range=[40, 50]), dict(metric='length.axon.int', value=100, sd=10), dict(metric='length.axon.int', value=80),
                                dict(metric='length.dendrite.pyr', value=None, range=None), dict(metric='length.dendrite.int', value=1, comparable=False), dict(metric='no.such.metric', value=3)])
        r, _ = stats.compute(tiny()); pm, tm = compare.rename_types(r, prof['type_map'], ['exc', 'inh'])
        st = [x['status'] for x in compare.compare(pm, prof)]
        self.assertEqual(st, ['pass', 'flag', 'pass', 'unknown', 'info', 'n/a'])     # 45 in [40,50]; 60 vs 100+-20; 60 within 50% of 80
    def test_profiles_load(self):
        for n in ('ca3', 'drosophila_mushroom_body', 'v1'):
            p = compare.load_profile(n); self.assertTrue(p['literature'])
            for e in p['literature']:
                for f in ('metric', 'reference', 'evidence', 'verified', 'derived_estimate'): self.assertIn(f, e, (n, e))

class TestAdapters(unittest.TestCase):
    def test_netmorph_roundtrip(self):
        d = tempfile.mkdtemp(); labs = ['100', '101', '102']; m = tiny()
        with open(os.path.join(d, 'x_net.txt.neurons'), 'w') as f:
            f.write('# header\n'); [f.write('%d,%s,%s,In,%g,%g,%g,5\n' % (i, labs[i], {'exc': 'pyramidal', 'inh': 'interneuron'}[TYPES[i]], *SOMA[i])) for i in range(3)]
        # node files: one root node per segment chain start; nodes keyed by coordinates
        nodes = {}; rows = {'rootnodes': [], 'continuationnodes': []}; nid = [0]
        def node(cell, kind, p, parent):
            key = (cell, kind, tuple(p))
            if key in nodes: return nodes[key]
            nid[0] += 1; nodes[key] = nid[0]
            if parent is None: rows['rootnodes'].append('%d,1,%s,%g,%g,%g,%s,0\n' % (nid[0], kind, *p, labs[cell]))
            else: rows['continuationnodes'].append('%d,1,%s,%g,%g,%g,%s,%d,0\n' % (nid[0], kind, *p, labs[cell], parent))
            return nid[0]
        for c, k, p0, p1 in SEGS:
            kn = 'axon' if k == AXON else 'dendrite'; a = nodes.get((c, kn, tuple(p0))) or node(c, kn, p0, None); node(c, kn, p1, a)
        for ext, r in rows.items(): open(os.path.join(d, 'x_net.txt.' + ext), 'w').write('# h\n' + ''.join(r))
        with open(os.path.join(d, 'x_net.txt.synapses'), 'w') as f:
            f.write('# h\n')
            for i, (a, b, s) in enumerate(SYN):
                f.write('%d,%s,1,1,1,1,1,1,0,0,%s,%s,0,BASAL\n' % (i, 'AMPAR' if s > 0 else 'GABAR', labs[a], labs[b]))
                if s > 0: f.write('%d,NMDAR,1,1,1,1,1,1,0,0,%s,%s,0,BASAL\n' % (i, labs[a], labs[b]))
        open(os.path.join(d, 'x_.nibr.clp'), 'w').write('regions=In;\nIn.shape=disc;\nIn.centerZ=0;\nIn.shape.radius=100;\nIn.shape.thickness=10;\n')
        self.assertTrue(io_netmorph.is_netmorph_dir(d)); n = io_netmorph.load(d)
        self.assertEqual(len(n.syn_pre), len(SYN)); self.assertAlmostEqual(n.region['volume_um3'], np.pi * 100 ** 2 * 10)
        r, _ = stats.compute(n); self.assertAlmostEqual(r['length.axon.pyramidal']['mean'], 45); self.assertAlmostEqual(r['targets.interneuron']['mean'], 2)

    def test_nes_duplicated_roundtrip(self):
        """synthetic NES file in the duplicated-geometry form found in the converted models: dend list == axon list (same cylinders)."""
        segs = [s for s in SEGS]; N = 3
        sph = []; cyl = []; sg = []; comp = []; flats = []; recs = []; box = []
        def add_geo(t, rec, lst): sg.append((t, 0, len(lst))); lst.append(rec); return len(sg) - 1
        lists = []
        for c in range(N):
            sid = add_geo(1, (0, len(sg), 1, SOMA[c], 5.0, c + 1), sph); comp.append(sid); soma_ids = [len(comp) - 1]
            mine = [s for s in segs if s[0] == c]; block = []
            for rep in range(2):          # duplicated: two identical blocks
                ids = []
                for (_, k, p0, p1) in mine:
                    g = add_geo(2, (0, len(sg), 2, [0, 0, 0], 1.0, p0, 1.0, p1, 0), cyl); comp.append(g); ids.append(len(comp) - 1)
                block.append(ids)
            lists.append((soma_ids, block[0], block[1], [s[1] for s in mine]))
        for (a, b, sgn) in SYN:   # receptor Src = a's axon comp (2nd block), Dst = b's dendrite comp (2nd block)
            ax = [i for i, k in zip(lists[a][2], lists[a][3]) if k == AXON][0]; de = [i for i, k in zip(lists[b][2], lists[b][3]) if k == DEND][0]
            bx = add_geo(3, (0, len(sg), 3, [1, 1, 1], [0.01] * 3, [0, 0, 0], 0), box)
            recs.append((len(recs), bx, ax, de, 0, 1, 3, 1, 1, 1, 0, (0, 0, 0), 0, 0, 0, 0, 0, 0, 0 if sgn > 0 else 1))
        for (soma_ids, d1, d2, _) in lists:
            name = b'cell\0'; hdr_len = 36; off_name = hdr_len; off_s = off_name + len(name); off_s += (-off_s) % 4
            off_d = off_s + 4 * len(soma_ids); off_a = off_d + 4 * len(d1); size = off_a + 4 * len(d2)
            buf = bytearray(size); struct.pack_into('<9I', buf, 0, size, len(name), off_name, len(soma_ids), off_s, len(d1), off_d, len(d2), off_a)
            buf[off_name:off_name + len(name)] = name
            for o, ids in ((off_s, soma_ids), (off_d, d1), (off_a, d2)): buf[o:o + 4 * len(ids)] = np.array(ids, '<i4').tobytes()
            flats.append(bytes(buf))
        p = tempfile.mktemp()
        with open(p, 'wb') as f:
            f.write(struct.pack('<i', 2)); f.write(struct.pack('<9Q', len(sg), len(sph), len(cyl), len(box), len(comp), len(recs), N, 0, 0))
            f.write(np.array(sg, io_nes.SG).tobytes())
            f.write(np.array([(0, i, s, c, r, pa) for (_, i, s, c, r, pa) in sph], io_nes.SPH).tobytes())
            f.write(np.array(cyl, io_nes.CYL).tobytes()); f.write(np.array(box, io_nes.BOX).tobytes())
            f.write(np.array([(i, g, (0,) * 6) for i, g in enumerate(comp)], io_nes.COMP).tobytes())
            f.write(np.array(recs, io_nes.REC).tobytes()); f.write(np.array([len(x) for x in flats], '<u4').tobytes()); [f.write(x) for x in flats]
        self.assertTrue(io_nes.is_nes_model(p)); m = io_nes.load(p)
        self.assertEqual(m.meta['geometry_mode'], 'duplicated'); self.assertEqual(len(m.seg_cell), len(SEGS))
        self.assertEqual(m.cell_type, ['excitatory', 'excitatory', 'inhibitory'])
        r, _ = stats.compute(m); self.assertAlmostEqual(r['length.axon.excitatory']['mean'], 45); self.assertAlmostEqual(r['length.dendrite.excitatory']['mean'], 20)
        self.assertAlmostEqual(r['syn_dendrite.inhibitory']['mean'], 1); self.assertAlmostEqual(r['targets.inhibitory']['mean'], 2)
        os.remove(p)

if __name__ == '__main__': unittest.main()
