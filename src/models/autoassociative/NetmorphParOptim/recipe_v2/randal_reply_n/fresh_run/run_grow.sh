#!/bin/bash
# usage: run_grow.sh "ARM:SEED ..." ; global gate: sims+growths across all workers on the patched instance < 3 ; growths of mine <= 2 ; 4 BLAS threads
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
tot() { pgrep -fc '[r]un_exp\.py|[f]r_dyn\.py|[g]en_autonm_labels\.py.*-Port 8010'; }
mine() { pgrep -fc '[g]en_autonm_labels\.py.*-Port 8010'; }
for j in $1; do
  a=${j%%:*}; s=${j##*:}
  [ -f grow_${a}_s${s}/result.txt ] && continue
  while [ $(tot) -ge 3 ] || [ $(mine) -ge 2 ]; do sleep 20; done
  date +%s > start_${a}_s${s}.txt
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 $PY grow_fr.py $a $s > launch_${a}_s${s}.log 2>&1 &
  sleep 45
done
wait; echo done > grow_$$.done
