#!/bin/bash
# repro_g restart stage: RST1 alone, then RST2+RST3 concurrently, fresh NES process.
cd /home/johnjose/cos/netmorph_work/recipe_v2/repro_g
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
run() { REP=$1 $PY grow_rep.py V1n30 31415 0.0175 0.0495 > launch_$1.log 2>&1; }
date +%s > start_RST1.txt; run RST1; date +%s > end_RST1.txt
for r in RST2 RST3; do date +%s > start_$r.txt; run $r & sleep 3; done
wait; echo done > rst.done
