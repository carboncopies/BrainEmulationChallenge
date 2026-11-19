#!/bin/bash
# gated queue: at most 3 run_sim.py at a time; order: c 0.15, 0, 1.5; designs sorted; GABA on then silenced
cd /home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nr() { pgrep -fc '[r]un_sim\.py '; }
for c in 0.15 0 1.5; do
  for f in design_*.json; do
    b=${f#design_}; b=${b%.json}; key=${b%%_*}; name=${b#*_}
    case $name in R42|R44) mode=rip;; *) mode=ov;; esac
    for sg in 0 1; do
      tag=${b}_c${c}_sg${sg}; [ -f raw_$tag.json ] && continue
      while [ $(nr) -ge 3 ]; do sleep 5; done
      $PY run_sim.py $tag $key $mode $f $c $sg > log_$tag.txt 2>&1 &
      sleep 8
    done
  done
done
wait; echo done > queue.done
