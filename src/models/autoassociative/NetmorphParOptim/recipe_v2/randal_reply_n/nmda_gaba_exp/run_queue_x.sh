#!/bin/bash
# post hoc history check (DEVIATIONS 6): runs after run_queue.sh finishes; same gating (max 3, NES alive)
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp
while pgrep -f "[r]un_queue\.sh" >/dev/null; do sleep 30; done
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nr() { pgrep -fc '[r]un_exp\.py '; }
for s in 33333 66666 77777; do for c in 0 1.5; do for r in 0.56 1; do tag=X_s${s}_c${c}_r${r}_f1; [ -f raw_$tag.json ] && continue
  while [ $(nr) -ge 3 ]; do sleep 5; done; ss -ltn | grep -q ":8011 " || { echo "$(date +%T) NES dead, X stops" >> queue.log; exit 1; }
  echo "$(date +%T) start $tag" >> queue.log; $PY run_exp.py X $s $c $r 1 > log_$tag.txt 2>&1 & sleep 6; done; done; done
$PY run_exp.py B 77777 1.5 1 1 > log_B_s77777_c1.5_r1_f1.txt 2>&1 &
wait; echo "$(date +%T) X done" >> queue.log
