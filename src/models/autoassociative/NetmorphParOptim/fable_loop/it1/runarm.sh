#!/bin/bash
X=$1
mkdir -p /home/johnjose/cos/netmorph_work/fable_loop/it1/run_$X && cd /home/johnjose/cos/netmorph_work/fable_loop/it1/run_$X
s=$(date +%s)
echo n | timeout -s TERM 900 /home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python /home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/gen_autonm_labels.py -excel /home/johnjose/cos/netmorph_work/fable_loop/it1/config.xlsx -out /home/johnjose/cos/netmorph_work/fable_loop/it1/out_$X.xlsx -modelfile /home/johnjose/cos/netmorph_work/fable_loop/it1/model_it1$X -modelname fable-it1$X -batchlimit 1 -vizdir /home/johnjose/cos/netmorph_work/fable_loop/it1/viz_$X > run.log 2>&1
echo "EXIT=$? WALL=$(($(date +%s)-s))" > result.txt
