#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing
P=$(cat ../ripple_S1_R3/pypath)
r(){ tag=$1; shift; $P run_inh.py "$tag" "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey > run_$tag.log; sleep 3; }
r P3_single_c0 P3 c0 full single
r P3_single_c015 P3 c0.15 full single
r P3_single_c025 P3 c0.25 full single
r P3_single_c05 P3 c0.5 full single
r P3_rip12 P3 c0.15 full rip:0123:12:1
r P3_rip12_SG P3 c0.15 SG rip:0123:12:1
r P3_rip12_IS P3 c0.15 IS rip:0123:12:1
r P3_single_c025_SG P3 c0.25 SG single
r P3_rip16 P3 c0.15 full rip:0123:16:1
r P3_rip20 P3 c0.15 full rip:0123:20:1
r P3_sh16 P3 c0.15 full rip:2031:16:1
echo done > batch_P3.done
