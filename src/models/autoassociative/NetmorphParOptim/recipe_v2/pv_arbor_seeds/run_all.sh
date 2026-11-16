#!/bin/bash
# 3 concurrent runs per batch; one batch per seed (S1,V1,V3). Usage: run_all.sh SEED...
cd /home/johnjose/cos/netmorph_work/recipe_v2/pv_arbor_seeds
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for seed in "$@"; do
  for v in S1 V1 V3; do $P grow_pv.py $v $seed > launch_${v}_s$seed.log 2>&1 & sleep 40; done
  wait
done
