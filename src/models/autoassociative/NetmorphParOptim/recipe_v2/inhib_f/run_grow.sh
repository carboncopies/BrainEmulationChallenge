#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/inhib_f
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
for s in 27182 31415; do for job in "V1n20 0.03" "V3n24 0.02" "V3n20 0.02"; do
  set -- $job
  while [ $(ng) -ge 3 ]; do sleep 20; done
  $PY grow_pv.py $1 $s 0.0175 $2 > launch_$1_s${s}_i$2.log 2>&1 &
  sleep 60
done; done
wait; echo done > grow.done
