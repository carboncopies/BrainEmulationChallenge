#!/bin/bash
S=$1; D=/home/johnjose/cos/netmorph_work/fable_loop/r2_it3/seed$S; cd $D
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:/home/johnjose/cos/netmorph_work/extra
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
DUMP=/home/johnjose/cos/netmorph_work/fable_loop/r2_seeds/viz_$S/sample_0000.json
( $PY ../step1.py $S 2>&1 | grep -v -i -E "authkey|jwt" > step1.log
grep -q "OK" step1.log && ! grep -q FAIL step1.log || { echo STEP1 FAILED >> step1.log; exit 1; }
ID=$(cat C_id.txt)
$PY ../run_phases.py -SimID $ID -dump $DUMP -phases phases.json -out out.json -cid C_id.txt 2>&1 | grep -v -i -E "authkey|jwt" > run.log
$PY forcecheck.py > forcecheck.log 2>&1; $PY summarize.py > /dev/null 2>summ.err ) 
echo done > DONE
