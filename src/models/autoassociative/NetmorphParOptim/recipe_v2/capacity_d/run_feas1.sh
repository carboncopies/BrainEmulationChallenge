#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/capacity_d
W=/home/johnjose/cos/netmorph_work/recipe_v2
for s in 16180 27182 31415; do echo "n30_D0.0175_s$s $W/linefix_c/grow_V1n30_s${s}_p0d0175_i0d0495/viz/sample_0000.json"; done > nets1.txt
for d in 0d01 0d021 0d05; do echo "V1_D${d}_s16180 $W/linefix_c/grow_V1_s16180_p${d}_i0d05/viz/sample_0000.json"; done >> nets1.txt
for v in S1 V1 V3; do echo "${v}_D1.5_s16180 $W/linefix/grow_${v}_s16180_fix/viz/sample_0000.json"; done >> nets1.txt
for v in S1 V1 V3; do for s in 31415 27182; do echo "${v}_D1.5_s$s $W/linefix_b/grow_${v}_s${s}_fix/viz/sample_0000.json"; done; done >> nets1.txt
for s in 16180 31415; do echo "n30_D1.5_s$s $W/linefix_b/grow_V1n30_s${s}_fix/viz/sample_0000.json"; done >> nets1.txt
while read t d; do [ -f "$d" ] || echo MISSING $t; python3 -u feas2.py $t $d > feas_$t.log 2>&1 & done < nets1.txt
wait; echo done > feas1.done
