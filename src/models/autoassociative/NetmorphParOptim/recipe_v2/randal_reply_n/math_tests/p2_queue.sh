#!/bin/bash
# Phase-2 queue. GATE: starts only when no fable-knobs growth process (gen_autonm_labels python) is running, as required by the task ("offline only until the batch ends").
# Then waves of 3 sims on my instance j0 (API port 8300); instance restarted between waves if NES RSS > 10 GB; every sim is deleted in p2_run's finally.
H=/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_tests; cd $H; PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
until [ "$(ps -eo args | grep -c '[b]in/python.*gen_autonm')" -eq 0 ]; do sleep 30; done
echo "gate open $(date)" >> p2_queue.log
WAVES=("BASE:66666 BASE:77777 W13:66666" "W13:77777 E20:66666 E20:77777" "CASC:66666 CASC:77777 LPS:66666" "LPS:77777 RN:66666 RN:77777")
for w in "${WAVES[@]}"; do
  pids=""
  for j in $w; do d=${j%%:*}; s=${j##*:}; [ -f rawP2_P2_${d}_s${s}.json ] && continue
    OMP_NUM_THREADS=1 $PY p2_run.py $s $d 8300 > log_p2_${d}_s${s}.txt 2>&1 &
    pids="$pids $!"; sleep 20; done
  for p in $pids; do wait $p; done
  rss=$(awk '/VmRSS/{print $2}' /proc/$(cat instances/j0/nes.pid)/status); echo "wave done $w rss_kB $rss $(date)" >> p2_queue.log
  if [ "${rss:-0}" -gt 10000000 ]; then ./inst.sh stop 0; sleep 3; ./inst.sh start 0; echo restarted >> p2_queue.log; fi
done
echo ALLDONE >> p2_queue.log
