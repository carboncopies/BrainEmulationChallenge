#!/bin/bash
# addendum B: gated queue, mine <= 2, total real sims (python procs of any worker) <= 3
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nm() { pgrep -fc 'python.* [r]un_pl\.py '; }
nt() { pgrep -fc 'python.* ([r]un_exp|[f]r_dyn|[d]yn[0-9]*|[r]un_pc|[r]un_pl)\.py '; }
alive() { ss -ltn | grep -q ":8011 "; }
job() { local tag="s$1_$2_r$3_f$4"; [ -f rawB_$tag.json ] && return
        while [ $(nm) -ge 2 ] || [ $(nt) -ge 3 ]; do sleep 10; done
        alive || { echo "$(date +%T) NES on 8011 not alive, queue B stops" >> queueB.log; exit 1; }
        echo "$(date +%T) start $tag (mine $(nm), total $(nt))" >> queueB.log; $PY run_pl.py $1 $2 $3 $4 > logB_$tag.txt 2>&1 & sleep 8; }
for s in 77777 66666; do for a in L0 LH; do for r in 1 0.56; do job $s $a $r 1; done; done; job $s LI 1 1; done
job 77777 L0 1 2
wait; echo "$(date +%T) queue B done" >> queueB.log
