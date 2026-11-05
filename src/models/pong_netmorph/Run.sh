#!/bin/bash
# Run the hand-wired Pong controller. Defaults to a local API on port 8000.
# Usage: ./Run.sh [-H host] [-P port] [-m truthtable|play] [-t ticks] [-s seed] [-k tick_ms] [-S spacing_ms] [-O outdir] [-M saved_model]
host="localhost"; port="8000"; mode="truthtable"; ticks="500"; seed="1"; tickms="20"; spacing="100"; outdir="output"; model=""
while getopts "H:P:m:t:s:k:S:O:M:" opt; do
  case ${opt} in
    H) host=$OPTARG ;;
    P) port=$OPTARG ;;
    m) mode=$OPTARG ;;
    t) ticks=$OPTARG ;;
    s) seed=$OPTARG ;;
    k) tickms=$OPTARG ;;
    S) spacing=$OPTARG ;;
    O) outdir=$OPTARG ;;
    M) model=$OPTARG ;;
    *) echo "Usage: $0 [-H host] [-P port] [-m truthtable|play] [-t ticks] [-s seed] [-k tick_ms] [-S spacing_ms] [-O outdir] [-M saved_model]"; exit 1 ;;
  esac
done
cd "$(dirname "$0")"
# Override with PYTHON=...; else the repo venv, else python3.
PY=${PYTHON:-../../../venv/bin/python}
[ -x "$PY" ] || PY=python3
exec $PY pong_handwired.py -Host "$host" -Port "$port" -Mode "$mode" -Ticks "$ticks" -Seed "$seed" -TickMs "$tickms" -SpacingMs "$spacing" -Out "$outdir" ${model:+-Model "$model"}
