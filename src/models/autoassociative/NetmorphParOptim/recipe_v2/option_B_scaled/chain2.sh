#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled
P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
while ! grep -q "^done" batch_R8.out; do sleep 5; done
$P batch.py R2 > batch_R2.out 2>&1
echo done > chain2.done
