#!/bin/bash
# usage: post_b1.sh SEED : prune, analyze (bars), feas, designs for a finished B1 growth
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python; s=$1; export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
$PY prune_fr.py $s
$PY analyze_fr.py B1_s$s B1P_s$s B1Q_s$s > analyze_$s.log 2>&1
./run_feas.sh "B1P_s$s B1Q_s$s B1_s$s"
$PY make_designs.py B1P_s$s > design_$s.log 2>&1
echo done > post_$s.done
