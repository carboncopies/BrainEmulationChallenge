#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/headline_h
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
for job in "V1n30 11111 0.0495" "V1n30 22222 0.0495" "V1n20 11111 0.03"; do
  set -- $job; date +%s > start_$1_s$2.txt
  $PY grow_pv.py $1 $2 0.0175 $3 > launch_$1_s$2.log 2>&1 &
  sleep 3
done
sleep 20
job="V1n20 22222 0.03"; set -- $job
while [ $(ng) -ge 3 ]; do sleep 20; done
date +%s > start_$1_s$2.txt
$PY grow_pv.py $1 $2 0.0175 $3 > launch_$1_s$2.log 2>&1 &
wait; echo done > grow.done
