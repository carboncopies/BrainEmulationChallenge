#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/capacity_d
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
ng() { pgrep -fc '[g]en_autonm_labels.py.*-Port 8010'; }
nm() { pgrep -fc '[d]yn2\.py '; }
slot() { while [ $(( $(ng) + $(nm) )) -ge 3 ]; do sleep 15; done; }
launch() { slot; tag=$1; shift; [ -f raw_$tag.json ] && return; $PY dyn2.py $tag "$@" > log_$tag.txt 2>&1 & sleep 25; }
for c in 0.15 0 1.5 3.0; do for net in p0d05_s16180 p0d035_s16180; do for d in D42 D44; do for sg in 0 1; do
  launch ${d}_${net}_c${c}_sg${sg} $net $d $c $sg single
done; done; done; done
for sg in 0 1; do for m in rip:0123:12 rip:0123:16 rip:2031:16; do
  launch RIP_${m//:/_}_p0d05_s16180_sg${sg} p0d05_s16180 D44 0.15 $sg $m
done; done
wait; echo done > dyn.done
