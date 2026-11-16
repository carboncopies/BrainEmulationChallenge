#!/bin/bash
# one batch: S1,V1,V3 at the given seed, D_synmax 0.15 on the 3 interneuron pairs, 3 concurrent
cd /home/johnjose/cos/netmorph_work/recipe_v2/pv_dsyn015
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for seed in "$@"; do
  for v in S1 V1 V3; do $P grow_pv.py $v $seed > launch_${v}_s${seed}_d015.log 2>&1 & sleep 40; done
  wait
done
