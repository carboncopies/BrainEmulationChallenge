#!/bin/bash
# Stage 2 batch 1: V1 with 30 interneurons, three seeds. usage: run_stage2a.sh DPP DI   (values fixed by PREREGISTRATION_stage2.md decision rule)
cd /home/johnjose/cos/netmorph_work/recipe_v2/linefix_c
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for s in 16180 31415 27182; do $P grow_pv_s2.py V1n30 $s $1 $2 > launch_V1n30_s${s}_p$1_i$2.log 2>&1 & sleep 40; done
wait
