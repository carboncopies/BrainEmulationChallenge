#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/capacity_d
for b in $(sed 's/BAD feas_//;s/.json//' bad.txt); do
  d=$(grep "^$b " nets1.txt | cut -d' ' -f2); [ -z "$d" ] && d=thr_V1_${b#thrV1_}.npy
  python3 -u feas2.py $b $d > feas_$b.log 2>&1 &
done; wait; echo done > feas1c.done
