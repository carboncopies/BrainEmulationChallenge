#!/bin/bash
# recall sims (dyn3.py), max 2 concurrent on the patched instance (growth sims + dyn3 < 3 never needed: growth finished)
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nm() { pgrep -fc '[d]yn3\.py '; }
launch() { while [ $(nm) -ge 2 ]; do sleep 10; done; tag=$1; shift; [ -f raw_$tag.json ] && return; OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 $PY dyn3.py $tag "$@" > log_$tag.txt 2>&1 & sleep 15; }
for c in 0.15 1.5; do for s in 33333 44444; do for a in B1R B2R B1 B2; do for d in D42 D44; do
  net=${a}_s$s; [ -f groups_${d}_${net}.json ] || continue
  launch ${d}_${net}_c${c} $net $d $c 0 single
done; done; done; done
wait; echo done > dyn_$$.done
