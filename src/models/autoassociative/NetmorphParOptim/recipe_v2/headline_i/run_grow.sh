#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/headline_i
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
for s in 33333 44444 55555; do
  date +%s > start_V1n20_s$s.txt
  $PY grow_pv.py V1n20 $s 0.0175 0.03 > launch_V1n20_s$s.log 2>&1 &
  sleep 3
done
sleep 20
for s in 66666 77777; do
  while [ $(ng) -ge 3 ]; do sleep 20; done
  date +%s > start_V1n20_s$s.txt
  $PY grow_pv.py V1n20 $s 0.0175 0.03 > launch_V1n20_s$s.log 2>&1 &
  sleep 30
done
wait; echo done > grow.done
