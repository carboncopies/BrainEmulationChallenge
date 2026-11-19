import sys, json, importlib.util
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
import ovlib as O
spec = importlib.util.spec_from_file_location('dyn2', '/home/johnjose/cos/netmorph_work/recipe_v2/headline_i/dyn2.py'); d2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(d2)
n_ok = 0
for key, gf in [('s33333', '../headline_i/groups_D42_V1n20_s33333.json'), ('s33333', '../headline_i/groups_D44_V1n20_s33333.json'), ('s77777', '../headline_i/groups_D42_V1n20_s77777.json')]:
    D, P = O.load(key); groups = d2.load_groups('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/' + gf)
    for c in (0.0, 0.15, 1.5):
        a = d2.pair_list(D, groups, c); b = O.pair_list_ov(D, groups, c)
        assert len(a) == len(b); assert all(x[:2] == y[:2] and abs(x[2] - y[2]) < 1e-9 for x, y in zip(a, b)), (key, gf, c); n_ok += 1
print('unit check identical for', n_ok, 'cases')
