#!/bin/bash
# usage: run_feas.sh "TAG ..." ; TAG = B1P_s33333 etc ; feas2 on the pruned/random/unpruned dump, 1 at a time (offline CPU)
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for t in $1; do [ -f feas_$t.json ] && continue; OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 $PY ../feas2.py $t grow_$t/viz/sample_0000.json > feas_$t.log 2>&1; done
