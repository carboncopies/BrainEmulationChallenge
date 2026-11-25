#!/bin/bash
# make_inst.sh K : create instance j<K> (copy of morph_tests2 i0 layout; ports 8300+10K .. +4; own out dir; models symlinked read-only from the linefix instance)
H=/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n; k=$1; d=$H/math_tests/instances/j$k; P=$((8300+10*k)); src=$H/morph_tests2/instances/i0
[ -d $d ] && { echo exists; exit 1; }
mkdir -p $d/nes $d/api $d/out/Admonishing/Models
for f in $src/nes/*; do b=$(basename $f); [ "$b" = NES.yaml ] && continue; cp -a $f $d/nes/$b; done
cp -a $src/api/BrainGenix-API $d/api/
sed -e "s/^Network_NES_API_Port:.*/Network_NES_API_Port: $((P+2))/" -e "s#^Output_BasePath:.*#Output_BasePath: $d/out#" $src/nes/NES.yaml > $d/nes/NES.yaml
sed -e "s/^Port=8200/Port=$P/" -e "s/^Port=8201/Port=$((P+1))/" -e "s/^Port=8202/Port=$((P+2))/" -e "s/^Port=8203/Port=$((P+3))/" -e "s/^Port=8204/Port=$((P+4))/" $src/api/API.cfg > $d/api/API.cfg
for s in 66666 77777; do ln -s /home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/Models/v2-hdi-V1n20_s${s}_p0d0175_i0d030000 $d/out/Admonishing/Models/; done
echo made $d ports $P; grep -n Port $d/api/API.cfg | tr '\n' ' '
cp -a $src/../Source $d/
