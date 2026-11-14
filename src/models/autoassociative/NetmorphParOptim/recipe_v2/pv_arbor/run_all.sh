#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/pv_arbor
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for grp in "V1 V2 V3" "V4 V5 V6"; do
  for v in $grp; do $P grow_pv.py $v > launch_$v.log 2>&1 & sleep 40; done
  wait
done
