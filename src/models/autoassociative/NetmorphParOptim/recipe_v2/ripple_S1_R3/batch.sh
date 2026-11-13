#!/bin/bash
P=$(cat pypath)
r(){ n=$1; shift; $P run_r3.py "$n" "$@" 2>&1 | tr '\r' '\n' | grep -v -e Waiting -e Warn -e _color -e AuthKey > run_$n.log; sleep 8; }
r s2_R3c0_SG R3_c0 1 single
r s3_P P_T18_L10_c0 0 single
r s4_P_SG P_T18_L10_c0 1 single
r s5_c015 R3_c0.15 0 single
r s6_rip12 R3_c0.15 0 rip:0123:12:1:rec
r s7_rip16 R3_c0.15 0 rip:0123:16:1
r s8_rip20 R3_c0.15 0 rip:0123:20:1:rec
r s9_sh16 R3_c0.15 0 rip:2031:16:1
r s10_rip12_dt01 R3_c0.15 0 rip:0123:12:0.1:rec
r s11_c015_3cell R3_c0.15 0 rip:0123:12:0.1:2
r s12_c025_3cell R3_c0.25 0 rip:0123:12:0.1:2
r s13_sub3 R3_c0.15 0 rip:012:16:1
r s14_c05_3cell R3_c0.5 0 rip:0123:12:0.1:2
r s15_c0_rip12 R3_c0 0 rip:0123:12:1
r s16_rip20_dt01 R3_c0.15 0 rip:0123:20:0.1:rec
r s17_rip12_SG R3_c0.15 1 rip:0123:12:1
echo done > batch.done
