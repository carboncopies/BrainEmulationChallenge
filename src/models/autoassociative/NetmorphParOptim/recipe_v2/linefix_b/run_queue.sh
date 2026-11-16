#!/bin/bash
# 3 concurrent runs max, staggered 40 s start gate. Queue order: longest first.
cd /home/johnjose/cos/netmorph_work/recipe_v2/linefix_b
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
job() { v=$1; seed=$2; exec 9>gate.lock; flock 9; $P grow_pv.py $v $seed > launch_${v}_s${seed}_fix.log 2>&1 & pid=$!; sleep 40; flock -u 9; wait $pid; }
export -f job; export P
printf '%s\n' "S1 31415" "S1 27182" "V1n30 16180" "V1 31415" "V1 27182" "V3 31415" "V3 27182" "V1n30 31415" | xargs -P 3 -L 1 bash -c 'job $0 $1'
