#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled
while [ ! -f chain2.done ]; do sleep 5; done
/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python batch.py R9 > batch_R9.out 2>&1
echo done > chain3.done
