#!/bin/bash
# runs dyn.py jobs; launches only while (growth sims on the instance + my sims) < 3, max 2 of mine at once
cd /home/johnjose/cos/netmorph_work/recipe_v2/dynamics_c
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
n_growth() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
n_mine() { pgrep -fc '[d]yn\.py '; }
for c in 0.15 0 0.6 1.5 3.0; do for s in 16180 27182; do for d in DA DB; do for sg in 0 1; do
  tag=${d}_s${s}_c${c}_sg${sg}
  [ -f raw_$tag.json ] && continue
  while [ $(( $(n_growth) + $(n_mine) )) -ge 3 ] || [ $(n_mine) -ge 2 ]; do sleep 20; done
  $PY dyn.py $tag $s $d $c $sg > log_$tag.txt 2>&1 &
  sleep 30
done; done; done; done
wait
echo ALLDONE > queue.done
