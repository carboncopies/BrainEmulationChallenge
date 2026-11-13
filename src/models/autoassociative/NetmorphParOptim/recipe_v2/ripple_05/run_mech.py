import sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
import mech_lib as M
for n in sys.argv[1:]:
    if n == 'E2b': M.run_experiment('E2', 'raw_mech_E2b.json', kept=M.EXP['E2b_fallback']['kept_interneurons_per_memory'], tag='b')
    else: M.run_experiment(n, 'raw_mech_%s.json' % n.split('_')[0])
    time.sleep(30)
