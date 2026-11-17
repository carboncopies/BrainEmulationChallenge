#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/capacity_d
while read t d; do
  if python3 -c "import json,sys;sys.exit(0 if json.load(open('feas_$t.json'))['sampled_LB'] else 1)"; then python3 -u feas2.py $t $d > feas_$t.log 2>&1 & fi
done < nets1.txt
wait; echo done > feas1b.done
