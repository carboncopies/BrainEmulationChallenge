#!/bin/bash
# Stage 1: V1 seed 16180, three D settings on the PATCHED instance (API 8010), 3 concurrent
cd /home/johnjose/cos/netmorph_work/recipe_v2/linefix_c
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for d in 0.021 0.01 0.05; do $P grow_pv.py V1 16180 $d 0.05 > launch_V1_s16180_p${d}_i0.05.log 2>&1 & sleep 40; done
wait
