#!/bin/bash
# Runs tasks A, D, C in order. One simulation at a time, 30 s pause between runs, memory guard inside the python code
# (stops if < 60 GB available). Requires the NES API on localhost:8000.
set -e
R=/home/johnjose/cos/netmorph_work/recipe
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for s in seed20240628 seed1001 seed1002 seed1003; do
  $PY $R/$s/apply.py        2>&1 | grep -v -i -E "authkey|jwt|Waiting For Simulation" | tee $R/$s/apply.log
  sleep 30
  $PY $R/$s/recall_test.py  2>&1 | grep -v -i -E "authkey|jwt|Waiting For Simulation" | tee $R/$s/recall.log
  sleep 30
done
$PY $R/run_sweeps.py 2>&1 | grep -v -i -E "authkey|jwt|Waiting For Simulation" | tee $R/sweeps.log
