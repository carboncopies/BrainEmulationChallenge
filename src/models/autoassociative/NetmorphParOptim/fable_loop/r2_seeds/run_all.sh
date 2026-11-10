#!/bin/bash
W=/home/johnjose/cos/netmorph_work; N=$W/bec/src/models/autoassociative; PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:$W/extra
cd $W/fable_loop/r2_seeds
for S in 1001 1002 1003; do
mkdir -p run_$S && cd run_$S
start=$(date +%s)
echo n | timeout -s TERM 900 $PY $N/gen_autonm_labels.py -excel $W/fable_loop/it1/config.xlsx -out $W/fable_loop/r2_seeds/out_$S.xlsx -modelfile $W/fable_loop/it1/model_it1a -modelname fable-r2-seed$S -randomseed $S -batchlimit 1 -vizdir $W/fable_loop/r2_seeds/viz_$S > run.log 2>&1
echo "EXIT=$? WALL=$(( $(date +%s) - start ))" > result.txt
cd ..
done
