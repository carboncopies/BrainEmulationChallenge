#!/bin/bash
# usage: run_dyn.sh NET...   (single runs for every design with a groups file; c 0.15 0 1.5 3.0 x GABA on/silenced); gate: growth sims + dyn2 < 3
cd /home/johnjose/cos/netmorph_work/recipe_v2/headline_i
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
nm() { pgrep -fc '[d]yn2\.py '; }
launch() { while [ $(( $(ng) + $(nm) )) -ge 3 ]; do sleep 15; done; tag=$1; shift; [ -f raw_$tag.json ] && return; $PY dyn2.py $tag "$@" > log_$tag.txt 2>&1 & sleep 25; }
for c in 0.15 0 1.5 3.0; do for net in "$@"; do for d in D42 D44; do for sg in 0 1; do
  [ -f groups_${d}_${net}.json ] || continue
  launch ${d}_${net}_c${c}_sg${sg} $net $d $c $sg single
done; done; done; done
wait; echo done > dyn_$$.done
