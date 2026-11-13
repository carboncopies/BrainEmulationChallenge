#!/bin/bash
# usage: run_part1.sh SEEDTAG (629|630). Requires models v2-arbor-S1-seedNNN0000 and dump grow_S1-seedNNN/viz/sample_0000.json, designs made with rdesign.py (tag s629/s630, K=4)
T=$1; P=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
HERE=/home/johnjose/cos/netmorph_work/recipe_v2/robustness_S1
DU=$HERE/grow_S1-seed$T/viz/sample_0000.json; M=v2-arbor-S1-seed${T}0000
cd $HERE; mkdir -p logs
r(){ n=$1; shift; $P rrun.py "s${T}_$n" $M $DU "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey | grep -v '^ *$' > logs/run_s${T}_$n.log; sleep 5; }
C0=pairs/pairs_s${T}_K4_c0.json; C15=pairs/pairs_s${T}_K4_c0.15.json
r single_c0 $C0 0 single
r single_c015 $C15 0 single
r rip12_c0 $C0 0 rip:0123:12:1
r rip12_c015 $C15 0 rip:0123:12:1
r rip16_c015 $C15 0 rip:0123:16:1
r rip20_c015 $C15 0 rip:0123:20:1
r sh16_c015 $C15 0 rip:2031:16:1
r rip12_c015_SG $C15 1 rip:0123:12:1
echo done > part1_$T.done
