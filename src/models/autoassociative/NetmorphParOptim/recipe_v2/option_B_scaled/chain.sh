#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
for r in R6 R7 R5; do $P batch.py $r > batch_$r.out 2>&1; done
echo chaindone > chain.done
