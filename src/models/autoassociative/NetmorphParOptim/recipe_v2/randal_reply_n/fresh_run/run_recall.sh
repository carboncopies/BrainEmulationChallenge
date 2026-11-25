#!/bin/bash
# usage: run_recall.sh "SEED ..." ; for each seed: pruned (B1P) and baseline, designs D42 and O1, c 0.15 and 1.5. Gate: total sims+growths < 3 (all workers).
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
R=/home/johnjose/cos/netmorph_work/recipe_v2
tot() { pgrep -fc '[r]un_exp\.py|[f]r_dyn\.py|[g]en_autonm_labels\.py.*-Port 8010'; }
launch() { tag=$1; [ -f raw_$tag.json ] && return; while [ $(tot) -ge 3 ]; do sleep 15; done
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 $PY fr_dyn.py "$@" > log_$tag.txt 2>&1 & sleep 20; }
for s in $1; do for c in 0.15 1.5; do for d in D42 O1; do
  [ -f design_${d}_B1P_s$s.json ] && launch ${d}_B1P_s${s}_c$c B1_s$s grow_B1P_s$s/viz/sample_0000.json design_${d}_B1P_s$s.json $c
  if [ $d = D42 ]; then bd=$R/headline_i/groups_D42_V1n20_s$s.json; else bd=$R/ripple_overlap_j/design_s${s}_F1.json; fi
  bdump=$R/headline_i/grow_V1n20_s${s}_p0d0175_i0d03/viz/sample_0000.json
  [ -f $bd ] && launch ${d}_base_s${s}_c$c base_s$s $bdump $bd $c
done; done; done
wait; echo done > recall_$$.done
