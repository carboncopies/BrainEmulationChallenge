#!/bin/bash
# usage: run_grow.sh "ARM:SEED ARM:SEED ..."  ; max 2 concurrent growth sims (pgrep gate on the patched port 8010), BLAS threads 4
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
for j in $1; do
  a=${j%%:*}; s=${j##*:}
  [ -f grow_${a}_s${s}/result.txt ] && continue
  while [ $(ng) -ge 2 ]; do sleep 20; done
  date +%s > start_${a}_s${s}.txt
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 $PY grow_arm.py $a $s > launch_${a}_s${s}.log 2>&1 &
  sleep 40
done
wait; echo done > grow_$$.done
