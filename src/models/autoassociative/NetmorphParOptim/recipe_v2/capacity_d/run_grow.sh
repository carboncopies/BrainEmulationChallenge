#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/capacity_d
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
for job in "16180 0.035" "16180 0.05" "27182 0.035" "27182 0.05"; do
  set -- $job
  while [ $(ng) -ge 3 ]; do sleep 20; done
  $PY grow_pv.py V1n30 $1 $2 0.0495 > launch_V1n30_s$1_p$2.log 2>&1 &
  sleep 60
done
wait; echo done > grow.done
