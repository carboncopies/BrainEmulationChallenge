#!/bin/bash
# gated queue, max 3 concurrent stdp_run.py processes (each = training sim then probe sim)
cd /home/johnjose/cos/netmorph_work/recipe_v2/stdp_k
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nr() { pgrep -fc '[s]tdp_run\.py [s]'; }
launch() { key=$1; arm=$2; R=$3; c=$4; tag=${key}_${arm}_R${R}_c${c}; [ -f raw_$tag.json ] && return
  while [ $(nr) -ge 3 ]; do sleep 5; done
  $PY stdp_run.py $key $arm $R $c > log_$tag.txt 2>&1 & sleep 8; }
KEYS="s16180 s27182 s31415 s11111 s22222 s33333 s44444 s55555 s66666 s77777"
for R in 10 100; do for c in 0.15 0; do for arm in A1 A2; do for k in $KEYS; do launch $k $arm $R $c; done; done; done; done
for c in 0.15 0; do for k in $KEYS; do launch $k A1 0 $c; done; done
wait; echo done > queue.done
