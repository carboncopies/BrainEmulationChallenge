#!/bin/bash
# Stage 2 batch 2: S1n30 / V3n30, seeds 16180 then 27182, pyramidal D 0.0175, interneuron D 0.04. Gate: fewer than 3 growth processes machine-wide.
cd /home/johnjose/cos/netmorph_work/recipe_v2/linefix_c
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for job in "S1n30 16180" "V3n30 16180" "S1n30 27182" "V3n30 27182"; do
  set -- $job
  while [ "$(pgrep -fc '[g]row_pv[a-z0-9_]*\.py')" -ge 3 ]; do sleep 20; done
  echo "$(date) start $1 $2 (growth procs before: $(pgrep -fc '[g]row_pv[a-z0-9_]*\.py'))"
  $P grow_pv_s2.py $1 $2 0.0175 0.04 > launch_$1_s$2_p0.0175_i0.04.log 2>&1 &
  sleep 45
done
wait; echo "$(date) all done"
