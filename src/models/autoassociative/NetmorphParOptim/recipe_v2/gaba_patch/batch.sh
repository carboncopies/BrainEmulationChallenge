#!/bin/bash
cd /home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch
P=$(cat ../ripple_S1_R3/pypath)
r(){ tag=$1; shift; $P run_g.py "$tag" "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey > run_$tag.log; sleep 5; }
for spec in "x5 v2-arbor-S1-gabax5 5" "x2 v2-arbor-S1-gabax2 2" "x2p5 v2-arbor-S1-gabax2p5 2.5"; do
 set -- $spec; f=$1; m=$2; k=$3
 r ${f}_single_c0     $m $k R3_c0 0 single
 r ${f}_single_c015   $m $k R3_c0.15 0 single
 r ${f}_rip12         $m $k R3_c0.15 0 rip:0123:12:1
 r ${f}_rip12_SG      $m $k R3_c0.15 1 rip:0123:12:1
 r ${f}_rip16         $m $k R3_c0.15 0 rip:0123:16:1
 r ${f}_rip20         $m $k R3_c0.15 0 rip:0123:20:1
 r ${f}_sh16          $m $k R3_c0.15 0 rip:2031:16:1
 if [ $f = x5 ]; then r ${f}_single_c0_SG $m $k R3_c0 1 single; fi
done
echo done > batch.done
