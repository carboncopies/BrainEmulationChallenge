#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nm() { pgrep -fc 'python.* [r]un_pw\.py '; }
nt() { pgrep -fc 'python.* ([r]un_exp|[f]r_dyn|[d]yn[0-9]*|[r]un_pc|[r]un_pl|[r]un_pw)\.py '; }
alive() { ss -ltn | grep -q ":8011 "; }
job() { local tag="s$1_$2_r1_f1"; [ -f rawC_$tag.json ] && return
        while [ $(nm) -ge 2 ] || [ $(nt) -ge 3 ]; do sleep 10; done
        alive || { echo "$(date +%T) NES not alive, queue C stops" >> queueC.log; exit 1; }
        echo "$(date +%T) start $tag (mine $(nm), total $(nt))" >> queueC.log; $PY run_pw.py $1 $2 1.0 1 > logC_$tag.txt 2>&1 & sleep 8; }
for a in W70 W50 H2; do for s in 77777 66666; do job $s $a; done; done
wait; echo "$(date +%T) queue C done" >> queueC.log
