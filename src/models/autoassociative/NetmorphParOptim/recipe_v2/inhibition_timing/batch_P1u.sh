#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing
P=$(cat ../ripple_S1_R3/pypath)
r(){ tag=$1; shift; $P run_inh.py "$tag" "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey > run_$tag.log; sleep 3; }
r P1u_single_c025 P1u c0.25 full single
r P1u_single_c05 P1u c0.5 full single
r P1u_single_c025_SG P1u c0.25 SG single
r P1u_rip12 P1u c0.15 full rip:0123:12:1
r P1u_rip12_SG P1u c0.15 SG rip:0123:12:1
r P2_rip12 P2 c0.15 full rip:0123:12:1
r P2_single_c025 P2 c0.25 full single
echo done > batch_P1u.done
