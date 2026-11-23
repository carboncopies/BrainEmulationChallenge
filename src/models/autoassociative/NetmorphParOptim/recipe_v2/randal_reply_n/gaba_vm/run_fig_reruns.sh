#!/bin/bash
# figure-only reruns (added after the first results, not preregistered): same as A_x1_c0 / A_sg_c0 but Vm recorded to 10.7 s; waits for the main queue (1 sim at a time)
cd /home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm
while pgrep -f 'run_queue.sh' > /dev/null; do sleep 15; done
GVM_VM_MS=10700 ./run_queue.sh "F_x1_c0:0:1:none:file F_sg_c0:0:sg:none:file"
