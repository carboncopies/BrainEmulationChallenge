#!/bin/bash
# gated queue: at most 2 run_pc.py of mine and total sims (mine + other workers' run_exp/dyn/recall) <= 3 on the patched instance. skips finished runs.
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nm() { pgrep -fc '[r]un_pc\.py '; }
no() { pgrep -fc 'python.* ([r]un_exp|[f]r_dyn|[d]yn[0-9]*)\.py '; }   # other workers real sims (python processes only)
alive() { ss -ltn | grep -q ":8011 "; }
nesrss() { ps -o rss= -p $(ss -ltnp 2>/dev/null | grep ":8011 " | grep -o "pid=[0-9]*" | head -1 | cut -d= -f2) 2>/dev/null; }
restart_nes() { local np=$(ss -ltnp 2>/dev/null | grep ":8011 " | grep -o "pid=[0-9]*" | head -1 | cut -d= -f2); local ap=$(ss -ltnp 2>/dev/null | grep "127.0.0.1:8010 " | grep -o "pid=[0-9]*" | head -1 | cut -d= -f2)
  [ -n "$np" ] && [ "$np" != 3156209 ] && kill $np; [ -n "$ap" ] && [ "$ap" != 1972355 ] && kill $ap; sleep 5
  ( cd /home/johnjose/BrainGenix/wt/nes-linefix/Binaries && source /home/johnjose/BrainGenix/BrainGenix-NES/venv/bin/activate && (setsid nohup ./BrainGenix-NES >> ../../linefix-instance/nes.log 2>&1 &) ); sleep 15
  ( cd /home/johnjose/BrainGenix/wt/linefix-instance/api && (setsid nohup ./BrainGenix-API >> ../api.log 2>&1 &) ); sleep 10; echo "$(date +%T) restarted: $(ss -ltnp 2>/dev/null | grep -E ':8011 |127.0.0.1:8010 ' | grep -o 'pid=[0-9]*' | tr '\n' ' ')" >> queue.log; }
job() { local tag="s$1_$2_r$3_f$4"; [ -f raw_$tag.json ] && return
        while [ $(nm) -ge 2 ] || [ $(( $(nm) + $(no) )) -ge 3 ]; do sleep 10; done
        if [ "$(nesrss)" -gt 14000000 ] 2>/dev/null; then while [ $(( $(nm) + $(no) )) -gt 0 ]; do sleep 10; done; echo "$(date +%T) NES rss $(nesrss) kB > 14 GB and no sim running, restarting separate build" >> queue.log; restart_nes; fi
        alive || { echo "$(date +%T) NES on 8011 not alive, queue stops" >> queue.log; exit 1; }
        echo "$(date +%T) start $tag (mine $(nm), others $(no), rss $(nesrss))" >> queue.log; $PY run_pc.py $1 $2 $3 $4 > log_$tag.txt 2>&1 & sleep 8; }
while pgrep -f '[r]un_pc\.py 33333 D0 1.0 1' >/dev/null; do sleep 10; done
for d in D0 D1 D2 DL; do for r in 1 0.56; do for f in 1 2; do job 33333 $d $r $f; done; done; done
for s in 66666 77777; do for d in D0 D1 D2 DL; do for r in 1 0.56; do job $s $d $r 1; done; done; done
wait; echo "$(date +%T) queue done" >> queue.log
