#!/bin/bash
# gated queue: at most 3 run_exp.py at a time on the patched instance (8010). order: A (s33333 first), C, B, then F. skips finished runs.
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nr() { pgrep -fc '[r]un_exp\.py '; }
alive() { pgrep -x BrainGenix-NES -a | grep -q . && ss -ltn | grep -q ":8011 "; }
nesrss() { ps -o rss= -p $(ss -ltnp 2>/dev/null | grep ":8011 " | grep -o "pid=[0-9]*" | cut -d= -f2) 2>/dev/null; }
restart_nes() { local np=$(ss -ltnp 2>/dev/null | grep ":8011 " | grep -o "pid=[0-9]*" | cut -d= -f2); local ap=$(ss -ltnp 2>/dev/null | grep "127.0.0.1:8010 " | grep -o "pid=[0-9]*" | cut -d= -f2)
  [ -n "$np" ] && [ "$np" != 3156209 ] && kill $np; [ -n "$ap" ] && [ "$ap" != 1972355 ] && kill $ap; sleep 5
  ( cd /home/johnjose/BrainGenix/wt/nes-linefix/Binaries && source /home/johnjose/BrainGenix/BrainGenix-NES/venv/bin/activate && (setsid nohup ./BrainGenix-NES >> ../../linefix-instance/nes.log 2>&1 &) ); sleep 15
  ( cd /home/johnjose/BrainGenix/wt/linefix-instance/api && (setsid nohup ./BrainGenix-API >> ../api.log 2>&1 &) ); sleep 10; echo "$(date +%T) restarted: $(ss -ltnp 2>/dev/null | grep -E ':8011 |127.0.0.1:8010 ' | grep -o 'pid=[0-9]*' | tr '\n' ' ')" >> queue.log; }
job() { local tag="$1_s$2_c$3_r$4_f$5"; [ -f raw_$tag.json ] && return; while [ $(nr) -ge 3 ]; do sleep 5; done
        if [ "$(nesrss)" -gt 10000000 ] 2>/dev/null; then while [ $(nr) -gt 0 ]; do sleep 5; done; echo "$(date +%T) NES rss $(nesrss) kB > 10 GB, restarting separate build" >> queue.log; restart_nes; fi
        alive || { echo "$(date +%T) NES on 8011 not alive, queue stops" >> queue.log; exit 1; }
        echo "$(date +%T) nes_rss_kB $(nesrss)" >> queue.log
        echo "$(date +%T) start $tag" >> queue.log; $PY run_exp.py $1 $2 $3 $4 $5 > log_$tag.txt 2>&1 & sleep 6; }
job A 33333 1.5 0 1; job A 33333 0 0 1
for s in 33333 66666 77777; do for c in 0 0.15 1.5 3; do for r in 0 0.56 1; do for f in 0 1 2 5; do job A $s $c $r $f; done; done; done; done
for s in 33333 66666 77777; do for c in 0 1.5; do for r in 0 0.56 1; do for f in 0 1 2 5; do job C $s $c $r $f; done; done; done; done
for s in 33333 66666 77777; do for c in 0 1.5; do for r in 0 0.56 1; do for f in 0 1; do job B $s $c $r $f; done; done; done; done
wait
for r in 0 0.56 1; do for f in 0 1; do job F 33333 1.5 $r $f; done; done
for f in 0 1; do job F 33333 0 0.56 $f; done
for f in 0 1 5; do job F 33333 3 0.56 $f; done
wait; echo "$(date +%T) queue done" >> queue.log
