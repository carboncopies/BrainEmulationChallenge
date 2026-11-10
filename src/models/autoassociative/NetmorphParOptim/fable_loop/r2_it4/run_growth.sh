#!/bin/bash
W=/home/johnjose/cos/netmorph_work; N=$W/bec/src/models/autoassociative; PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:$W/extra
for X in d03 d07; do
cd $W/fable_loop/r2_it4/$X/grow
start=$(date +%s)
echo n | timeout -s TERM 900 $PY $N/gen_autonm_labels.py -excel $W/fable_loop/it1/config.xlsx -out $W/fable_loop/r2_it4/out_$X.xlsx -modelfile $W/fable_loop/r2_it4/model_$X -modelname fable-r2it4-$X -batchlimit 1 -vizdir $W/fable_loop/r2_it4/viz_$X > run.log 2>&1
echo "EXIT=$? WALL=$(( $(date +%s) - start ))" > result.txt
done
