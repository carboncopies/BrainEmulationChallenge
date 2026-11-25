#!/bin/bash
# REAL nesfarm test: 2 NES+API instances on high ports, 2 trivial jobs each (create + delete a tiny sim), guard, clean, down.
# Then checks: no leftover process in the test farm, ports free, protected PIDs (and other experiments' PIDs) untouched.
# Everything runs pinned to 4 CPUs (taskset), so NES threads inherit that affinity.
# usage: NESFARM_TEST_BUILD=<NES build dir> tests/real_test.sh [base_port=8900] [cpus=60-63]
# Needs a working nesfarm config (api_binary, users_json) in ~/.config/nesfarm.json or $NESFARM_CONFIG.
set -u
PKG=$(cd "$(dirname "$0")/.." && pwd)
BASE=${1:-8900}; CPUS=${2:-60-63}
BUILD=${NESFARM_TEST_BUILD:?set NESFARM_TEST_BUILD to an NES build dir}
SRC_CFG=${NESFARM_CONFIG:-$HOME/.config/nesfarm.json}
WORK=$(mktemp -d "${TMPDIR:-/tmp}/nesfarm_real_XXXX")
python3 - "$SRC_CFG" "$WORK" <<'E'
import json, sys
c = json.load(open(sys.argv[1])); c['farm_root'] = sys.argv[2] + '/farm'; json.dump(c, open(sys.argv[2] + '/cfg.json', 'w'), indent=1)
E
export NESFARM_CONFIG=$WORK/cfg.json
NF="taskset -c $CPUS python3 $PKG/nesfarm.py"
PROT=$(python3 -c "import json;print(' '.join(map(str,json.load(open('$NESFARM_CONFIG'))['protected_pids'])))")
snap() { for p in $PROT; do echo "$p $(awk '{print $22}' /proc/$p/stat 2>/dev/null || echo gone)"; done
         pgrep -x BrainGenix-NES | sort -n | tr '\n' ' '; echo; pgrep -x BrainGenix-API | sort -n | tr '\n' ' '; echo; }
before=$(snap)
fail=0; step() { echo; echo "=== $*"; }
check() { if eval "$1"; then echo "PASS: $2"; else echo "FAIL: $2"; fail=1; fi; }

step "up (2 instances, ports $BASE..$((BASE+14)), cpus $CPUS)"
$NF up --build "$BUILD" --n 2 --base-port $BASE --tag rt || { echo "FAIL: up"; fail=1; }
step status; $NF status --tag rt

cat > $WORK/jobs.json <<E
{"defaults": {"cmd": ["python3", "$PKG/examples/health_job.py", "--port", "{port}", "--hold", "12"]},
 "jobs": [{"name": "h0"}, {"name": "h1"}, {"name": "h2"}, {"name": "h3"}]}
E
step "run --dry-run"; $NF run --tag rt --job-file $WORK/jobs.json --dry-run
step "run (4 jobs, max 3 per instance)"; $NF run --tag rt --job-file $WORK/jobs.json; rc=$?
check "[ $rc -eq 0 ]" "4 jobs finished rc=0"
for j in h0 h1 h2 h3; do echo "$j: $(python3 -c "import json;s=json.load(open('$WORK/farm/rt/jobs/$j/status.json'));print('i%d port %d rc %s'%(s['instance'],s['port'],s['rc']))") | $(tr '\n' ' ' < $WORK/farm/rt/jobs/$j/job.log)"; done
n0=$(grep -l '"instance": 0' $WORK/farm/rt/jobs/*/status.json | wc -l); n1=$(grep -l '"instance": 1' $WORK/farm/rt/jobs/*/status.json | wc -l)
check "[ $n0 -eq 2 ] && [ $n1 -eq 2 ]" "jobs spread 2 + 2 over the instances (got $n0 + $n1)"
ov=$(python3 - $WORK/farm/rt/jobs <<'P'
import json, sys, glob, datetime as D
iv = [tuple(D.datetime.strptime(json.load(open(f))[k], '%Y-%m-%d %H:%M:%S') for k in ('start', 'end')) for f in glob.glob(sys.argv[1] + '/*/status.json')]
print(max(sum(1 for a, b in iv if a <= t < b) for t, _ in iv))
P
)
check "[ $ov -ge 2 ]" "jobs ran concurrently (max $ov at once)"
step "run again (all done: nothing to do)"; $NF run --tag rt --job-file $WORK/jobs.json | tail -1
step "guard --once"; $NF guard --tag rt --once
step "clean (ids 0..5)"; $NF clean --tag rt --max-id 5 --timeout 10
step "down --dry-run"; $NF down --tag rt --dry-run
step down; $NF down --tag rt; check "[ $? -eq 0 ]" "down rc=0"

step "leftover checks"
sleep 2
left=$(for p in $(ls /proc | grep -E '^[0-9]+$'); do c=$(readlink /proc/$p/cwd 2>/dev/null); case "$c" in $WORK/*) echo $p;; esac; done)
check "[ -z \"$left\" ]" "no process left with cwd in the test farm (${left:-none})"
busy=$(for p in $(seq $BASE $((BASE+14))); do ss -ltn "( sport = :$p )" | grep -q LISTEN && echo $p; done)
check "[ -z \"$busy\" ]" "ports $BASE..$((BASE+14)) free (${busy:-all free})"
after=$(snap)
prot_after=$(echo "$after" | head -n $(echo $PROT | wc -w)); prot_before=$(echo "$before" | head -n $(echo $PROT | wc -w))
check "[ \"$prot_before\" = \"$prot_after\" ]" "protected PIDs untouched (pid starttime): $(echo $prot_after | tr '\n' ' ')"
check "[ \"$before\" = \"$after\" ]" "set of BrainGenix-NES/API PIDs on the machine identical before and after"
echo; [ $fail -eq 0 ] && echo "REAL TEST PASSED (state kept in $WORK)" || echo "REAL TEST FAILED (state in $WORK)"
exit $fail
