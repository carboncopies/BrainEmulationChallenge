#!/bin/bash
# usage: run_queue.sh "TAG:C:GABA:KNOB:PROG ..."  -- strictly one simulation at a time (sequential), skips finished tags
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for j in $1; do
  IFS=: read tag c g k p <<< "$j"
  [ -f raw_${tag}.json ] && continue
  echo "$(date +%T) start $tag" >> queue.log
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $PY run_vm.py $tag $c $g $k $p > log_${tag}.txt 2>&1
  echo "$(date +%T) end $tag rc $?" >> queue.log
done
echo done > queue_$$.done
