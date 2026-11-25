#!/bin/bash
# neuron_reset_ahp queue (PREREGISTRATION_C.md). Total simulations across ALL workers <= 3 (python sim processes on the patched instance).
# Separate build only: restart when RSS > 10 GB and no simulation runs. Main NES 3156209 / API 1972355 never touched.
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
nt() { pgrep -fc 'python.* ([r]un_exp|[f]r_dyn|[d]yn[0-9]*|[r]un_pc|[r]un_pl|[r]un_pw|[r]un_nr|[r]un_nr2|[r]un_nr3|[r]un_vm)\.py '; }
alive() { ss -ltn | grep -q ":8011 "; }
nespid() { ss -ltnp 2>/dev/null | grep ":8011 " | grep -o "pid=[0-9]*" | cut -d= -f2; }
nesrss() { local p=$(nespid); [ -n "$p" ] && awk '/VmRSS/{print $2}' /proc/$p/status || echo 0; }
restart_nes() { local np=$(nespid); local ap=$(ss -ltnp 2>/dev/null | grep "127.0.0.1:8010 " | grep -o "pid=[0-9]*" | cut -d= -f2)
  [ -n "$np" ] && [ "$np" != 3156209 ] && kill $np; [ -n "$ap" ] && [ "$ap" != 1972355 ] && kill $ap; sleep 5
  ( cd /home/johnjose/BrainGenix/wt/nes-linefix/Binaries && source /home/johnjose/BrainGenix/BrainGenix-NES/venv/bin/activate && (setsid nohup ./BrainGenix-NES >> ../../linefix-instance/nes.log 2>&1 &) ); sleep 15
  ( cd /home/johnjose/BrainGenix/wt/linefix-instance/api && (setsid nohup ./BrainGenix-API >> ../api.log 2>&1 &) ); sleep 10
  echo "$(date +%T) restarted separate build: $(ss -ltnp 2>/dev/null | grep -E ':8011 |127.0.0.1:8010 ' | grep -o 'pid=[0-9]*' | tr '\n' ' ')" >> queueC.log; }
maybe_restart() { if [ "$(nesrss)" -gt 10000000 ] 2>/dev/null; then while [ $(nt) -gt 0 ]; do sleep 10; done
  echo "$(date +%T) NES rss $(nesrss) kB > 10 GB and no sim running: restart" >> queueC.log; restart_nes; fi; }
job() { local tag="C_$1_s$2_cue$3"; [ -f rawC_$tag.json ] && return
  while [ $(nt) -ge 3 ]; do sleep 10; done; maybe_restart
  while [ $(nt) -ge 3 ]; do sleep 10; done
  alive || { echo "$(date +%T) NES on 8011 not alive, queue stops" >> queueC.log; exit 1; }
  echo "$(date +%T) start $tag (sims running $(nt), rss $(nesrss) kB)" >> queueC.log
  $PY run_nr3.py $1 $2 $3 > log_$tag.txt 2>&1 & sleep 10; }
# PREREGISTRATION_C: C1 (2-spike cue, E16) then C2 (rho grid, single cue)
job E16 77777 2; job E16 66666 2; job E16.7 77777 1; job E16.7 66666 1; job E16.9 77777 1; job E16.9 66666 1; job E17.1 77777 1; job E17.1 66666 1
wait; echo "$(date +%T) queue C done" >> queueC.log
