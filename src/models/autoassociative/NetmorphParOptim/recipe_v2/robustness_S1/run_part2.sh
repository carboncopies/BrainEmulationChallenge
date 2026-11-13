#!/bin/bash
# Part 2: S1 (seed 20240628) K=5,6 (and an alternative K=4 design) ; apply-then-run, one sim per call, each deleted in the script
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
DU=/home/johnjose/cos/netmorph_work/recipe_v2/dendrite_rerun/grow_S1/viz/sample_0000.json
r(){ n=$1; shift; $P rrun.py "$n" v2-arbor-S10000 $DU "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey | grep -v '^ *$' > logs/run_$n.log; sleep 5; }
mkdir -p logs
r S1_K4alt_rip12 pairs/pairs_S1_K4_c0.15.json 0 rip:0123:12:1
for K in 5 6; do
 O=$(seq -s '' 0 $((K-1)))
 r S1_K${K}_single_c015 pairs/pairs_S1_K${K}_c0.15.json 0 single
 r S1_K${K}_rip12_c015 pairs/pairs_S1_K${K}_c0.15.json 0 rip:$O:12:1
 r S1_K${K}_rip12_cue3 pairs/pairs_S1_K${K}_c0.15.json 0 rip:$O:12:1:2
done
echo done > part2.done
