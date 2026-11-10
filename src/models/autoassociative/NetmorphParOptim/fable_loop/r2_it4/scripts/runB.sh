#!/bin/bash
W=/home/johnjose/cos/netmorph_work; R=$W/fable_loop/r2_it4
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient:$W/extra; PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
cd $R/scripts
for X in d03 d07; do
 GID=$(grep -o 'NES_SIM_ID=[0-9]*' $R/$X/grow/run.log | cut -d= -f2)
 ( $PY step1.py $X 2>&1 | grep -vi "authkey\|jwt" > $R/$X/step1.log )
 grep -q "OK$" $R/$X/step1.log || { echo "$X step1 not OK" > $R/$X/B_status.txt; continue; }
 CID=$(cat $R/$X/C_id.txt); [ "$CID" != "$GID" ] || { echo "ID clash" > $R/$X/B_status.txt; continue; }
 $PY run_phases.py -SimID $CID -dump $R/viz_$X/sample_0000.json -phases $R/$X/phases.json -out $R/$X/out.json -cid $R/$X/C_id.txt 2>&1 | grep -vi "authkey\|jwt" > $R/$X/run.log
 $PY forcecheck.py $X > $R/$X/forcecheck.log 2>&1
 $PY summarize.py $X > $R/$X/summarize.log 2>&1
 echo done > $R/$X/B_status.txt
done
echo ALLDONE > $R/B_all.txt
