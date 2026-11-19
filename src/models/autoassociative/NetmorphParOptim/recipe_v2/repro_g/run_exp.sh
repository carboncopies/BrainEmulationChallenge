#!/bin/bash
# repro_g experiment: V1n30 s31415 p0.0175 i0.0495. SEQ1-3 one at a time, then CON1-3 simultaneously, same NES process.
cd /home/johnjose/cos/netmorph_work/recipe_v2/repro_g
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
run() { REP=$1 $PY grow_rep.py V1n30 31415 0.0175 0.0495 > launch_$1.log 2>&1; }
for r in SEQ1 SEQ2 SEQ3; do date +%s > start_$r.txt; run $r; date +%s > end_$r.txt; done
for r in CON1 CON2 CON3; do date +%s > start_$r.txt; run $r & sleep 3; done
wait
for r in CON1 CON2 CON3; do date +%s > end_$r.txt; done
echo done > exp1.done
